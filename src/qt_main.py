#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QFrame, QSpinBox, QComboBox, QRadioButton, QButtonGroup, QGroupBox,
    QSplitter, QDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon

print("Importing database...")
from utils.database import Database
print("Importing autocomplete...")
from utils.autocomplete import AutocompleteLineEdit

print("Starting application...")

class EntryDialog(QDialog):
    """Fenêtre de saisie d'une nouvelle entrée."""
    
    def __init__(self, parent=None, db=None):
        print("Initializing EntryDialog...")
        super().__init__(parent)
        self.db = db
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setup_ui()
        print("EntryDialog initialized")
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        print("Setting up EntryDialog UI...")
        self.setWindowTitle("Nouvelle entrée")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Projet
        project_layout = QHBoxLayout()
        project_label = QLabel("Projet:")
        self.project_input = AutocompleteLineEdit(self.db.get_project_suggestions(), self)
        
        # Bouton clear dans un layout séparé
        clear_button_layout = QHBoxLayout()
        clear_button = QPushButton("✕")
        clear_button.setFixedWidth(30)
        clear_button.clicked.connect(self.clear_project_ticket)
        clear_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Empêche la tabulation sur ce bouton
        clear_button_layout.addWidget(clear_button)
        clear_button_layout.addStretch()
        
        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_input)
        layout.addLayout(project_layout)
        layout.addLayout(clear_button_layout)
        
        # Ticket
        ticket_layout = QHBoxLayout()
        ticket_label = QLabel("Ticket:")
        self.ticket_input = AutocompleteLineEdit(self.db.get_ticket_suggestions(), self)
        ticket_layout.addWidget(ticket_label)
        ticket_layout.addWidget(self.ticket_input)
        layout.addLayout(ticket_layout)
        
        # Description
        description_label = QLabel("Description:")
        self.description_input = QTextEdit()
        self.description_input.setTabStopDistance(20)
        self.description_input.setMinimumHeight(100)
        layout.addWidget(description_label)
        layout.addWidget(self.description_input)
        
        # Durée
        duration_layout = QHBoxLayout()
        duration_label = QLabel("Durée (heures):")
        self.duration_input = QSpinBox()
        self.duration_input.setRange(0, 24)
        self.duration_input.setValue(1)
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_input)
        duration_layout.addStretch()
        layout.addLayout(duration_layout)
        
        # Bouton Sauvegarder
        save_button = QPushButton("Sauvegarder")
        save_button.clicked.connect(self.save_entry)
        layout.addWidget(save_button)
        
        self.setLayout(layout)
        print("EntryDialog UI set up")
    
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
                    project_item.setText(2, f"{total_duration}h")
                    
                    for entry in project_entries:
                        entry_item = QTreeWidgetItem(project_item)
                        entry_item.setText(0, "")  # Projet déjà affiché dans le parent
                        entry_item.setText(1, entry.get('ticket_number', ''))
                        entry_item.setText(2, f"{entry.get('duration', 0)}h")
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
                    date_item.setText(2, f"{total_duration}h")
                    
                    for entry in date_entries:
                        entry_timestamp = datetime.fromisoformat(entry.get('timestamp'))
                        entry_item = QTreeWidgetItem(date_item)
                        entry_item.setText(0, entry.get('project_name', ''))
                        entry_item.setText(1, entry.get('ticket_number', ''))
                        entry_item.setText(2, f"{entry.get('duration', 0)}h")
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
                    project_item.setText(2, f"{total_duration}h")
                    
                    for entry in entries:
                        entry_timestamp = datetime.fromisoformat(entry.get('timestamp'))
                        entry_item = QTreeWidgetItem(project_item)
                        entry_item.setText(0, "")  # Projet déjà affiché dans le parent
                        entry_item.setText(1, entry.get('ticket_number', ''))
                        entry_item.setText(2, f"{entry.get('duration', 0)}h")
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
        self.setup_ui()
        self.setup_timer()
        print("LogTrackerApp initialized")
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        print("Setting up LogTrackerApp UI...")
        self.setWindowTitle("LogTracker")
        self.setFixedSize(300, 100)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Résumé
        self.summary_label = QLabel("Aucune entrée aujourd'hui")
        layout.addWidget(self.summary_label)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        new_entry_button = QPushButton("Nouvelle entrée")
        new_entry_button.clicked.connect(self.show_entry_dialog)
        buttons_layout.addWidget(new_entry_button)
        
        view_entries_button = QPushButton("Voir les entrées")
        view_entries_button.clicked.connect(self.show_entries_dialog)
        buttons_layout.addWidget(view_entries_button)
        
        layout.addLayout(buttons_layout)
        
        # Met à jour le résumé
        self.update_summary()
        print("LogTrackerApp UI set up")
    
    def setup_timer(self):
        """Configure le timer pour les rappels."""
        print("Setting up timer...")
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_last_entry)
        self.timer.start(30 * 60 * 1000)
        print("Timer set up")
    
    def update_summary(self):
        """Met à jour le résumé des entrées."""
        print("Updating summary...")
        try:
            # Récupère les entrées du jour
            today = datetime.now().date()
            entries = self.db.get_entries_for_day(today)
            
            if entries:
                # Dernière entrée (première de la liste car triée par ordre décroissant)
                last_entry = entries[0]
                time_str = datetime.fromisoformat(last_entry['timestamp']).strftime("%H:%M")
                
                # Temps total
                total_time = sum(entry['duration'] or 0 for entry in entries)
                hours = total_time // 60
                minutes = total_time % 60
                
                # Affiche tout sur une ligne
                summary_text = f"Dernier : {time_str} | aujourd'hui {hours}h{minutes:02d}"
                self.summary_label.setText(summary_text)
            else:
                self.summary_label.setText("Aucune entrée aujourd'hui")
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
