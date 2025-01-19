#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QFrame, QSpinBox, QComboBox, QRadioButton, QButtonGroup, QGroupBox,
    QSplitter, QDialog, QFormLayout, QStyle, QToolButton, QDialogButtonBox, QMessageBox,
    QDateEdit, QTimeEdit
)
from PyQt6.QtCore import Qt, QTimer, QSize, QDate, QTime
from PyQt6.QtGui import QFont, QIcon, QPainter, QColor, QPalette
import os
import json

from utils.database import Database
from utils.autocomplete import AutocompleteLineEdit
from ui.ticket_combo import TicketComboBox
from ui.project_combo import ProjectComboBox
from ui.config_dialog import ConfigDialog
from ui.sync_dialog import SyncDialog
from ui.entry_dialog import EntryDialog
from ui.entries_dialog import EntriesDialog
from ui.projects_dialog import ProjectsDialog

class LogTrackerApp(QMainWindow):
    """Fenêtre principale de l'application."""

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.entry_dialog = None
        self.entries_dialog = None
        self.config_dialog = None
        self.sync_dialog = None
        self.projects_dialog = None
        self.last_entry_time = None
        self.total_duration = 0
        self.load_config()
        self.setup_ui()
        self.setup_timer()

    def load_config(self):
        """Charge la configuration."""
        config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.start_time = datetime.strptime(config.get('start_time', '08:00'), '%H:%M').time()
                self.end_time = datetime.strptime(config.get('end_time', '18:00'), '%H:%M').time()
                self.daily_hours = int(self.db.get_setting('daily_hours', '8'))
        else:
            self.start_time = datetime.strptime('08:00', '%H:%M').time()
            self.end_time = datetime.strptime('18:00', '%H:%M').time()
            self.daily_hours = 8

    def load_svg_icon(self, filename):
        """Charge une icône SVG depuis le dossier resources."""
        try:
            # Déterminer le chemin de base en fonction du contexte (exe ou développement)
            if getattr(sys, 'frozen', False):
                # Si nous sommes dans l'exe
                base_path = sys._MEIPASS
                resources_dir = 'resources'
            else:
                # Si nous sommes en développement
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                resources_dir = os.path.join('src', 'resources')

            # Construire le chemin complet vers l'icône
            icon_path = os.path.join(base_path, resources_dir, filename)
            
            # Vérifier si le fichier existe
            if not os.path.exists(icon_path):
                print(f"Icône non trouvée : {icon_path}")
                return QIcon()
    
            # Charger et retourner l'icône
            return QIcon(icon_path)
        except Exception as e:
            print(f"Erreur lors du chargement de l'icône {filename}: {str(e)}")
            return QIcon()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Log Tracker")
        self.resize(300, 100)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("""\
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
        add_button = create_tool_button('plus.svg', "Ajouter une entrée", self.show_entry_dialog)
        list_button = create_tool_button('list.svg', "Voir les entrées", self.show_entries_dialog)
        self.sync_button = create_tool_button('refresh.svg', "Synchroniser vers jira", self.show_sync_dialog)
        config_button = create_tool_button('settings.svg', "Configuration", self.show_config_dialog)
        projects_button = create_tool_button('projects.svg', "Projets", self.show_projects_dialog)

        # Met à jour l'état du bouton de synchronisation
        self.update_sync_button_state()

        # Ajout des boutons à la barre d'outils
        toolbar.addWidget(add_button)
        toolbar.addWidget(list_button)
        toolbar.addWidget(self.sync_button)
        toolbar.addStretch()
        toolbar.addWidget(config_button)
        toolbar.addWidget(projects_button)

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
        self.current_time_label.setToolTip("Temps depuis la dernière saisie")
        clock_icon.setToolTip("Temps depuis la dernière saisie")
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
        self.total_time_label.setToolTip("Temps saisie sur la journée")
        total_icon.setToolTip("Temps saisie sur la journée")
        total_time_layout.addWidget(total_icon)
        total_time_layout.addWidget(self.total_time_label)
        
        # Temps non synchronisé avec icône refresh-off.svg
        unsync_time_layout = QHBoxLayout()
        unsync_time_layout.setSpacing(5)
        
        # Création de l'icône refresh-off colorée
        unsync_icon = QLabel()
        unsync_pixmap = self.load_svg_icon('refresh-off.svg').pixmap(QSize(14, 14))
        painter = QPainter(unsync_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(unsync_pixmap.rect(), QColor("#d0d0d1"))
        painter.end()
        unsync_icon.setPixmap(unsync_pixmap)
        
        self.unsync_time_label = QLabel("0h00")
        self.unsync_time_label.setToolTip("Temps non encore synchronisé")
        unsync_icon.setToolTip("Temps non encore synchronisé")
        unsync_time_layout.addWidget(unsync_icon)
        unsync_time_layout.addWidget(self.unsync_time_label)

        info_layout.addLayout(current_time_layout)
        info_layout.addWidget(QLabel(" | "))  # Séparateur vertical
        info_layout.addLayout(total_time_layout)
        info_layout.addWidget(QLabel(" | "))  # Séparateur vertical
        info_layout.addLayout(unsync_time_layout)
        info_layout.addStretch()
        
        main_layout.addLayout(info_layout)

    def update_sync_button_state(self):
        """Met à jour l'état du bouton de synchronisation en fonction de la configuration Jira."""
        config = self.db.get_jira_config()
        is_configured = all(config.get(key) for key in ['jira_base_url', 'jira_email', 'jira_token'])
        self.sync_button.setEnabled(is_configured)
        if not is_configured:
            self.sync_button.setToolTip("Jira n'est pas configuré. Allez dans les paramètres pour le configurer.")
        else:
            self.sync_button.setToolTip("Synchroniser vers Jira")

    def setup_timer(self):
        """Configure le timer pour les vérifications périodiques."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_alerts)
        self.timer.timeout.connect(self.update_summary)
        self.timer.start(60000)  # Vérifie toutes les minutes
        self.update_summary()

    def check_alerts(self):
        """Vérifie les conditions d'alerte et met à jour l'interface."""
        current_time = datetime.now().time()
        current_date = datetime.now().date()

        # Réinitialisation quotidienne
        if self.last_entry_time and self.last_entry_time.date() != current_date:
            self.last_entry_time = None
            self.total_duration = 0

        # Vérifie si on est dans les heures de travail
        if current_time < self.start_time or current_time > self.end_time:
            self.set_background_color("black")
            return

        # Calcul du temps d'inactivité
        if self.last_entry_time:
            inactive_time = datetime.now() - self.last_entry_time
            inactive_hours = inactive_time.total_seconds() / 3600

            if inactive_hours >= 2:
                self.set_background_color("darkred")
            elif inactive_hours >= 1:
                self.set_background_color("darkorange")
            else:
                self.set_background_color("black")
        else:
            # Si aucune entrée aujourd'hui et dans les heures de travail
            self.set_background_color("darkorange")

        # Alerte de fin de journée
        end_datetime = datetime.combine(current_date, self.end_time)
        time_left = end_datetime - datetime.now()
        if time_left.total_seconds() <= 1800 and self.total_duration < self.daily_hours * 60:  # 30 minutes
            self.set_background_color("darkred")

    def set_background_color(self, color):
        """Change la couleur de fond de la fenêtre."""
        palette = self.palette()
        if color == "black":
            palette.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        elif color == "darkorange":
            palette.setColor(QPalette.ColorRole.Window, QColor("#FF8C00").darker(150))
        elif color == "darkred":
            palette.setColor(QPalette.ColorRole.Window, QColor("#8B0000"))
        self.setPalette(palette)

    def update_summary(self):
        """Met à jour le résumé des entrées."""
        try:
            # Récupère les entrées du jour
            today = datetime.now().date()
            entries = self.db.get_entries_for_day(today)
            
            # Calcule le temps total
            total_minutes = sum(entry['duration'] or 0 for entry in entries)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if hours > 0:
                self.total_time_label.setText(f"{hours}h{minutes:02d}")
            else:
                self.total_time_label.setText(f"{minutes}m")
            
            # Calcule le temps non synchronisé
            unsync_entries = self.db.get_unsynchronized_entries()
            unsync_minutes = sum(entry['duration'] or 0 for entry in unsync_entries)
            unsync_hours = unsync_minutes // 60
            unsync_mins = unsync_minutes % 60
            if unsync_hours > 0:
                self.unsync_time_label.setText(f"{unsync_hours}h{unsync_mins:02d}")
            else:
                self.unsync_time_label.setText(f"{unsync_mins}m")

            # Met à jour le temps écoulé depuis la dernière entrée
            if entries:
                last_entry = entries[0]  # Dernière entrée
                last_time = datetime.strptime(f"{last_entry['date']} {last_entry['time']}", "%Y-%m-%d %H:%M")
                elapsed_minutes = int((datetime.now() - last_time).total_seconds() / 60)
                hours = elapsed_minutes // 60
                minutes = elapsed_minutes % 60
                
                if hours > 0:
                    self.current_time_label.setText(f"{hours}h{minutes:02d}")
                else:
                    self.current_time_label.setText(f"{minutes}m")
            else:
                self.current_time_label.setText("00:00")
        except Exception as e:
            print(f"Erreur lors de la mise à jour du résumé : {str(e)}")

    def show_entry_dialog(self):
        """Affiche la fenêtre de saisie."""
        if self.entry_dialog is not None:
            self.entry_dialog.close()
        self.entry_dialog = EntryDialog(self, self.db)

        if self.entry_dialog.exec() == QDialog.DialogCode.Accepted:
            self.last_entry_time = datetime.now()
            self.update_summary()

    def show_entries_dialog(self):
        """Affiche la fenêtre des entrées."""
        if not self.entries_dialog:
            self.entries_dialog = EntriesDialog(self, self.db)
        self.entries_dialog.update_entries_view()  # Rafraîchit à chaque ouverture
        self.entries_dialog.show()
        self.entries_dialog.raise_()

    def show_config_dialog(self):
        """Affiche la fenêtre de configuration."""
        if self.config_dialog is not None:
            self.config_dialog.close()
        self.config_dialog = ConfigDialog(self)
        if self.config_dialog.exec():
            self.update_sync_button_state()
    
    def show_sync_dialog(self):
        """Affiche la fenêtre de synchronisation."""
        if not self.sync_dialog:
            self.sync_dialog = SyncDialog(self)
        self.sync_dialog.load_entries()  # Rafraîchit à chaque ouverture
        self.sync_dialog.show()
        self.sync_dialog.raise_()

    def show_projects_dialog(self):
        """Affiche la fenêtre de gestion des projets."""
        if self.projects_dialog is not None:
            self.projects_dialog.close()
        self.projects_dialog = ProjectsDialog(self, self.db)
        self.projects_dialog.exec()

    def check_last_entry(self):
        """Vérifie la dernière entrée et affiche une notification si nécessaire."""
        try:
            today = datetime.now().date()
            entries = self.db.get_entries_for_day(today)

            if not entries:
                # TODO: Implémenter les notifications système
                return

            last_entry = entries[0]
            last_time = datetime.strptime(f"{last_entry['date']} {last_entry['time']}", "%Y-%m-%d %H:%M")

            if datetime.now() - last_time > timedelta(minutes=30):
                # TODO: Implémenter les notifications système
                return

        except Exception as e:
            print(f"Erreur lors de la vérification de la dernière entrée : {str(e)}")


def main():
    """Point d'entrée de l'application."""
    app = QApplication(sys.argv)
    window = LogTrackerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
