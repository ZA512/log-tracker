#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QFrame, QSpinBox, QComboBox, QRadioButton, QButtonGroup, QGroupBox,
    QSplitter, QDialog, QFormLayout, QStyle, QToolButton
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QPainter, QColor
import os

print("Importing database...")
from utils.database import Database
print("Importing autocomplete...")
from utils.autocomplete import AutocompleteLineEdit
from ui.ticket_combo import TicketComboBox
from ui.project_combo import ProjectComboBox
from ui.config_dialog import ConfigDialog

print("Starting application...")

class EntryDialog(QDialog):
    """Fenêtre de saisie d'une nouvelle entrée."""

    def __init__(self, parent=None, db=None):
        print("Initializing EntryDialog...")
        super().__init__(parent)
        self.db = db
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setup_ui()
        self.reset_fields()  # Réinitialise tous les champs
        print("EntryDialog initialized")

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        print("Setting up EntryDialog UI...")
        self.setWindowTitle("Nouvelle entrée")
        self.setModal(True)
        self.resize(500, 400)

        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setSpacing(5)  # Réduit l'espace entre les éléments
        
        # Projet avec bouton X
        project_widget = QWidget()
        project_layout = QHBoxLayout(project_widget)
        project_layout.setContentsMargins(0, 0, 0, 0)
        project_layout.setSpacing(5)
        
        self.project_input = ProjectComboBox()
        clear_button = QPushButton("✕")
        clear_button.setFixedWidth(30)
        clear_button.clicked.connect(self.clear_project_ticket)
        clear_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        project_layout.addWidget(self.project_input)
        project_layout.addWidget(clear_button)
        
        form_layout.addRow("Projet:", project_widget)
        
        # Ticket
        self.ticket_input = TicketComboBox()
        form_layout.addRow("Ticket:", self.ticket_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMinimumHeight(100)
        form_layout.addRow("Description:", self.description_input)
        
        # Durée avec label "minutes" à droite et boutons de raccourcis
        duration_widget = QWidget()
        duration_layout = QVBoxLayout(duration_widget)
        duration_layout.setContentsMargins(0, 0, 0, 0)
        duration_layout.setSpacing(5)
        
        # Ligne avec le spinbox et le label minutes
        spinbox_layout = QHBoxLayout()
        spinbox_layout.setSpacing(5)
        
        self.duration_input = QSpinBox()
        self.duration_input.setMinimum(1)
        self.duration_input.setMaximum(999)
        self.duration_input.setValue(60)  # Valeur par défaut : 60 minutes
        
        minutes_label = QLabel("minutes")
        
        spinbox_layout.addWidget(self.duration_input)
        spinbox_layout.addWidget(minutes_label)
        spinbox_layout.addStretch()
        
        duration_layout.addLayout(spinbox_layout)
        
        # Ligne avec les boutons de raccourcis
        shortcuts_layout = QHBoxLayout()
        shortcuts_layout.setSpacing(5)
        
        # Fonction pour créer un bouton de raccourci
        def create_shortcut_button(text, minutes):
            btn = QPushButton(text)
            btn.setFixedWidth(45)
            btn.clicked.connect(lambda: self.duration_input.setValue(minutes))
            return btn
        
        # Ajout des boutons de raccourcis
        shortcuts = [
            ("15m", 15),
            ("30m", 30),
            ("1h", 60),
            ("2h", 120),
            ("3h", 180),
            ("4h", 240),
            ("5h", 300),
            ("6h", 360),
            ("7h", 420),
            ("8h", 480)
        ]
        
        for text, minutes in shortcuts:
            shortcuts_layout.addWidget(create_shortcut_button(text, minutes))
        
        shortcuts_layout.addStretch()
        duration_layout.addLayout(shortcuts_layout)
        
        form_layout.addRow("Durée:", duration_widget)
        
        main_layout.addLayout(form_layout)
        
        # Bouton Sauvegarder
        save_button = QPushButton("Sauvegarder")
        save_button.clicked.connect(self.save_entry)
        main_layout.addWidget(save_button)
        
        self.setLayout(main_layout)
        print("EntryDialog UI set up")

        # Initialise la liste des projets
        self.project_input.set_projects(self.db.get_project_suggestions())

        # Connecte le changement de projet à la mise à jour des tickets
        self.project_input.projectChanged.connect(self.update_tickets)

    def reset_fields(self):
        """Réinitialise tous les champs du formulaire."""
        self.project_input.clear()
        self.ticket_input.clear()
        self.description_input.clear()
        self.duration_input.setValue(60)  # Valeur par défaut : 60 minutes

    def clear_project_ticket(self):
        """Efface les champs projet et ticket."""
        print("Clearing project and ticket fields...")
        self.project_input.clear()
        self.ticket_input.clear()
        print("Project and ticket fields cleared")

    def save_entry(self):
        """Sauvegarde l'entrée dans la base de données."""
        print("Saving entry...")
        description = self.description_input.toPlainText().strip()
        if not description:
            print("No description, skipping save...")
            return
            
        project = self.project_input.text().strip()
        ticket = self.ticket_input.text().strip()
        duration = self.duration_input.value()
        
        try:
            # Sauvegarde dans la base de données
            self.db.add_entry(
                description=description,
                project_id=project if project else None,
                ticket_id=ticket if ticket else None,
                duration=duration
            )
            
            print("Entry saved successfully")
            self.accept()  # Ferme la fenêtre
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {str(e)}")
            # Ici vous pourriez ajouter une boîte de dialogue d'erreur

    def update_tickets(self):
        """Met à jour la liste des tickets en fonction du projet sélectionné."""
        project_name = self.project_input.text().strip()
        if project_name:
            # Récupère l'ID du projet
            project = self.db.get_project_by_name(project_name)
            if project:
                # Récupère les tickets du projet
                ticket_numbers = self.db.get_project_tickets(project['id'])
                
                # Récupère le dernier ticket utilisé
                last_ticket = self.db.get_last_ticket(project['id'])
                current_ticket = last_ticket['ticket_number'] if last_ticket else None
                
                # Met à jour la liste des tickets
                self.ticket_input.set_tickets(ticket_numbers, current_ticket)
        else:
            # Si pas de projet, efface les tickets
            self.ticket_input.set_tickets([])

    def show(self):
        """Affiche la fenêtre après avoir réinitialisé les champs."""
        self.reset_fields()
        super().show()

    def exec(self):
        """Exécute la fenêtre après avoir réinitialisé les champs."""
        self.reset_fields()
        return super().exec()


class EntriesDialog(QDialog):
    """Fenêtre d'affichage des entrées."""

    def __init__(self, parent=None, db=None):
        print("Initializing EntriesDialog...")
        super().__init__(parent)
        self.db = db
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setup_ui()
        self.update_entries_view()
        print("EntriesDialog initialized")

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        print("Setting up EntriesDialog UI...")
        self.setWindowTitle("Entrées")
        self.resize(800, 500)

        # Layout principal
        layout = QVBoxLayout()

        # Contrôles dans un layout horizontal
        controls_layout = QHBoxLayout()

        # Groupe de boutons radio pour la période
        period_group = QGroupBox("Période")
        period_layout = QHBoxLayout()
        self.period_day = QRadioButton("Journée")
        self.period_8days = QRadioButton("8 jours")
        self.period_day.setChecked(True)
        period_layout.addWidget(self.period_day)
        period_layout.addWidget(self.period_8days)
        period_group.setLayout(period_layout)
        controls_layout.addWidget(period_group)

        # Groupe de boutons radio pour le type de vue
        self.view_group = QGroupBox("Présentation")
        self.view_group.setVisible(False)
        view_layout = QHBoxLayout()
        self.view_by_day = QRadioButton("Jour par jour")
        self.view_by_project = QRadioButton("Par projet")
        self.view_by_day.setChecked(True)
        view_layout.addWidget(self.view_by_day)
        view_layout.addWidget(self.view_by_project)
        self.view_group.setLayout(view_layout)
        controls_layout.addWidget(self.view_group)

        # Ajoute un stretch pour que les groupes restent à gauche
        controls_layout.addStretch()

        # Ajoute les contrôles au layout principal
        layout.addLayout(controls_layout)

        # Configuration du QTreeWidget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Projet", "Ticket", "Durée", "Description", ""])  # Colonne vide pour le retour à la ligne
        self.tree.setColumnWidth(0, 150)  # Projet
        self.tree.setColumnWidth(1, 100)  # Ticket
        self.tree.setColumnWidth(2, 80)   # Durée
        self.tree.setColumnWidth(3, 400)  # Description
        self.tree.setColumnWidth(4, 10)   # Colonne vide
        self.tree.setWordWrap(True)
        layout.addWidget(self.tree)

        self.setLayout(layout)
        print("EntriesDialog UI set up")

        # Connexion des signaux
        self.period_day.toggled.connect(self.update_entries_view)
        self.period_8days.toggled.connect(lambda checked: self.view_group.setVisible(checked))
        self.view_by_day.toggled.connect(self.update_entries_view)
        self.view_by_project.toggled.connect(self.update_entries_view)

    def update_entries_view(self):
        """Met à jour l'affichage des entrées."""
        print("Updating entries view...")
        self.tree.clear()

        # Calcul de la période
        today = datetime.now().date()
        if self.period_day.isChecked():
            start_date = today
            end_date = today
        else:
            start_date = today - timedelta(days=7)
            end_date = today

        try:
            if self.period_day.isChecked():
                # Vue journée groupée par projet
                entries = self.db.get_entries_by_date_range(start_date, end_date)
                if not entries:
                    print("No entries for today")
                    return

                # Organise les entrées par projet
                entries_by_project = {}
                for entry in entries:
                    project = entry.get('project_name', 'Sans projet')
                    if project not in entries_by_project:
                        entries_by_project[project] = []
                    entries_by_project[project].append(entry)

                # Crée les éléments de l'arbre
                for project, project_entries in entries_by_project.items():
                    project_item = QTreeWidgetItem(self.tree)
                    project_item.setText(0, project)
                    total_duration = sum(entry.get('duration', 0) for entry in project_entries)
                    project_item.setText(2, f"{total_duration}m")

                    for entry in project_entries:
                        entry_item = QTreeWidgetItem(project_item)
                        entry_item.setText(0, "")  # Projet déjà affiché dans le parent
                        entry_item.setText(1, entry.get('ticket_number', ''))
                        entry_item.setText(2, f"{entry.get('duration', 0)}m")
                        entry_item.setText(3, entry.get('description', ''))

                self.tree.expandAll()

            elif self.view_by_day.isChecked():
                # Vue sur 8 jours chronologique
                entries = self.db.get_entries_by_date_range(start_date, end_date)
                if not entries:
                    print("No entries for the last 8 days")
                    return

                # Organise les entrées par date
                entries_by_date = {}
                for entry in entries:
                    entry_timestamp = datetime.fromisoformat(entry.get('timestamp'))
                    entry_date = entry_timestamp.date()
                    if entry_date not in entries_by_date:
                        entries_by_date[entry_date] = []
                    entries_by_date[entry_date].append(entry)

                # Noms des jours en français
                jours = {
                    0: 'Lundi',
                    1: 'Mardi',
                    2: 'Mercredi',
                    3: 'Jeudi',
                    4: 'Vendredi',
                    5: 'Samedi',
                    6: 'Dimanche'
                }

                # Crée les éléments de l'arbre
                for date in sorted(entries_by_date.keys(), reverse=True):
                    date_entries = entries_by_date[date]
                    jour = jours[date.weekday()]
                    date_item = QTreeWidgetItem(self.tree)
                    date_item.setText(0, f"{jour} {date.strftime('%d/%m/%Y')}")
                    total_duration = sum(entry.get('duration', 0) for entry in date_entries)
                    date_item.setText(2, f"{total_duration}m")

                    for entry in date_entries:
                        entry_timestamp = datetime.fromisoformat(entry.get('timestamp'))
                        entry_item = QTreeWidgetItem(date_item)
                        entry_item.setText(0, entry.get('project_name', ''))
                        entry_item.setText(1, entry.get('ticket_number', ''))
                        entry_item.setText(2, f"{entry.get('duration', 0)}m")
                        entry_item.setText(3, f"{entry_timestamp.strftime('%H:%M')} - {entry.get('description', '')}")

                self.tree.expandAll()

            else:  # Vue par projet sur 8 jours
                entries_by_project = self.db.get_entries_by_project(start_date, end_date)
                if not entries_by_project:
                    print("No entries for the last 8 days")
                    return

                for project_name, entries in entries_by_project.items():
                    project_item = QTreeWidgetItem(self.tree)
                    project_item.setText(0, project_name or 'Sans projet')
                    total_duration = sum(entry.get('duration', 0) for entry in entries)
                    project_item.setText(2, f"{total_duration}m")

                    for entry in entries:
                        entry_timestamp = datetime.fromisoformat(entry.get('timestamp'))
                        entry_item = QTreeWidgetItem(project_item)
                        entry_item.setText(0, "")  # Projet déjà affiché dans le parent
                        entry_item.setText(1, entry.get('ticket_number', ''))
                        entry_item.setText(2, f"{entry.get('duration', 0)}m")
                        entry_item.setText(3, f"{entry_timestamp.strftime('%d/%m %H:%M')} - {entry.get('description', '')}")

                self.tree.expandAll()

        except Exception as e:
            print(f"Erreur lors de la mise à jour de la vue : {str(e)}")
            import traceback
            traceback.print_exc()


class LogTrackerApp(QMainWindow):
    """Fenêtre principale de l'application."""

    def __init__(self):
        print("Initializing LogTrackerApp...")
        super().__init__()
        self.db = Database()
        self.entry_dialog = None
        self.entries_dialog = None
        self.config_dialog = None
        self.setup_ui()
        self.setup_timer()
        print("LogTrackerApp initialized")

    def load_svg_icon(self, filename):
        """Charge une icône SVG depuis le dossier resources."""
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'resources', filename)
        return QIcon(path)

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Log Tracker")
        self.resize(300, 100)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #d0d0d1;
            }
            QToolButton {
                border: none;
                padding: 5px;
                color: #d0d0d1;
            }
            QToolButton:hover {
                background-color: #333333;
                border-radius: 3px;
            }
            QLabel {
                color: #d0d0d1;
                font-size: 13px;
                background: transparent;
            }
            QFrame[frameShape="4"] {  /* HLine */
                background-color: #333333;
                max-height: 1px;
                border: none;
            }
        """)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)  # Réduit l'espacement vertical

        # Barre d'outils supérieure
        toolbar = QHBoxLayout()
        toolbar.setSpacing(2)

        # Fonction pour créer un bouton avec une icône SVG colorée
        def create_tool_button(icon_name, tooltip, callback):
            button = QToolButton()
            icon = self.load_svg_icon(icon_name)
            # Force la couleur de l'icône en blanc
            pixmap = icon.pixmap(QSize(16, 16))
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor("#d0d0d1"))
            painter.end()
            button.setIcon(QIcon(pixmap))
            button.setIconSize(QSize(16, 16))
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            return button

        # Création des boutons avec les icônes colorées
        add_button = create_tool_button('plus.svg', "Nouvelle entrée", self.show_entry_dialog)
        list_button = create_tool_button('list.svg', "Voir les entrées", self.show_entries_dialog)
        config_button = create_tool_button('settings.svg', "Configuration", self.show_config_dialog)

        # Ajout des boutons à la barre d'outils
        toolbar.addWidget(add_button)
        toolbar.addWidget(list_button)
        toolbar.addStretch()
        toolbar.addWidget(config_button)

        main_layout.addLayout(toolbar)

        # Zone d'information avec icônes
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 5, 0, 5)
        
        # Temps actuel avec icône d'horloge
        current_time_layout = QHBoxLayout()
        current_time_layout.setSpacing(5)
        
        # Création de l'icône d'horloge colorée
        clock_icon = QLabel()
        clock_pixmap = self.load_svg_icon('clock.svg').pixmap(QSize(14, 14))
        painter = QPainter(clock_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(clock_pixmap.rect(), QColor("#d0d0d1"))
        painter.end()
        clock_icon.setPixmap(clock_pixmap)
        
        self.current_time_label = QLabel("00:00")
        current_time_layout.addWidget(clock_icon)
        current_time_layout.addWidget(self.current_time_label)
        
        # Temps total avec icône de somme
        total_time_layout = QHBoxLayout()
        total_time_layout.setSpacing(5)
        
        # Création de l'icône sigma colorée
        total_icon = QLabel()
        sigma_pixmap = self.load_svg_icon('sigma.svg').pixmap(QSize(14, 14))
        painter = QPainter(sigma_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(sigma_pixmap.rect(), QColor("#d0d0d1"))
        painter.end()
        total_icon.setPixmap(sigma_pixmap)
        
        self.total_time_label = QLabel("0h00")
        total_time_layout.addWidget(total_icon)
        total_time_layout.addWidget(self.total_time_label)
        
        info_layout.addLayout(current_time_layout)
        info_layout.addWidget(QLabel(" | "))  # Séparateur vertical
        info_layout.addLayout(total_time_layout)
        info_layout.addStretch()
        
        main_layout.addLayout(info_layout)

    def setup_timer(self):
        """Configure le timer pour les rappels."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_last_entry)
        self.timer.timeout.connect(self.update_summary)  # Ajout de la mise à jour du résumé
        self.timer.start(60000)  # Vérifie toutes les minutes
        self.update_summary()  # Met à jour immédiatement au démarrage

    def update_summary(self):
        """Met à jour le résumé des entrées."""
        try:
            # Récupère les entrées du jour
            today = datetime.now().date()
            entries = self.db.get_entries_for_day(today)

            # Calcul du temps total
            total_time = sum(entry['duration'] or 0 for entry in entries)
            hours = total_time // 60
            minutes = total_time % 60
            self.total_time_label.setText(f"{hours}h{minutes:02d}")

            # Mise à jour du temps actuel
            if entries:
                last_entry = entries[0]  # Dernière entrée
                last_time = datetime.fromisoformat(last_entry['timestamp'])
                elapsed_minutes = int((datetime.now() - last_time).total_seconds() / 60)
                hours = elapsed_minutes // 60
                minutes = elapsed_minutes % 60
                self.current_time_label.setText(f"{hours:02d}:{minutes:02d}")
            else:
                self.current_time_label.setText("00:00")
        except Exception as e:
            print(f"Erreur lors de la mise à jour du résumé : {str(e)}")

    def show_entry_dialog(self):
        """Affiche la fenêtre de saisie."""
        print("Showing entry dialog...")
        if self.entry_dialog is None:
            self.entry_dialog = EntryDialog(self, self.db)

        if self.entry_dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_summary()

    def show_entries_dialog(self):
        """Affiche la fenêtre des entrées."""
        print("Showing entries dialog...")
        if self.entries_dialog is None:
            self.entries_dialog = EntriesDialog(self, self.db)
        self.entries_dialog.show()

    def show_config_dialog(self):
        """Affiche la fenêtre de configuration."""
        if not self.config_dialog:
            self.config_dialog = ConfigDialog(self)
        self.config_dialog.show()

    def check_last_entry(self):
        """Vérifie la dernière entrée et affiche une notification si nécessaire."""
        print("Checking last entry...")
        try:
            today = datetime.now().date()
            entries = self.db.get_entries_for_day(today)

            if not entries:
                # TODO: Implémenter les notifications système
                print("Pensez à saisir vos activités !")
                return

            last_entry = entries[0]
            last_time = datetime.fromisoformat(last_entry['timestamp'])

            if datetime.now() - last_time > timedelta(minutes=30):
                # TODO: Implémenter les notifications système
                print("Pensez à saisir vos activités !")

        except Exception as e:
            print(f"Erreur lors de la vérification de la dernière entrée : {str(e)}")


def main():
    """Point d'entrée de l'application."""
    print("Creating QApplication...")
    app = QApplication(sys.argv)
    print("Creating main window...")
    window = LogTrackerApp()
    print("Showing main window...")
    window.show()
    print("Starting event loop...")
    sys.exit(app.exec())

if __name__ == '__main__':
    print("Starting main()...")
    main()
