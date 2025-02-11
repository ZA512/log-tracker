#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QFrame, QSpinBox, QComboBox, QRadioButton, QButtonGroup, QGroupBox,
    QSplitter, QDialog, QFormLayout, QStyle, QToolButton, QDialogButtonBox, QMessageBox,
    QDateEdit, QTimeEdit, QStatusBar, QMenuBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QSize, QDate, QTime
from PyQt6.QtGui import QFont, QIcon, QPainter, QColor, QPalette, QAction
import os
import json

from utils.database import Database
from utils.autocomplete import AutocompleteLineEdit
from utils.jira_client import JiraClient
from ui.ticket_combo import TicketComboBox
from ui.project_combo import ProjectComboBox
from ui.config_dialog import ConfigDialog
from ui.sync_dialog import SyncDialog
from ui.entry_dialog import EntryDialog
from ui.entry_dialog_v2 import EntryDialogV2
from ui.entries_dialog import EntriesDialog
from ui.projects_dialog import ProjectsDialog
from ui.create_ticket_dialog import CreateTicketDialog
from ui.theme import Theme, DEFAULT_THEME, DARK_THEME

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
        self.jira_client = None  # Sera initialisé lors de la configuration
        self.last_entry_time = None
        self.total_duration = 0
        
        # État de l'alerte
        self.alert_state = "normal"
        
        self.load_config()
        self.setup_ui()
        self.setup_timer()
        
        # Initialise last_entry_time avec la dernière entrée
        try:
            entries = self.db.get_entries_for_day(datetime.now().date())
            if entries:
                last_entry = entries[0]  # La première entrée est la plus récente
                self.last_entry_time = datetime.strptime(f"{last_entry['date']} {last_entry['time']}", "%Y-%m-%d %H:%M")
        except Exception as e:
            print(f"Erreur lors de l'initialisation de last_entry_time : {str(e)}")
            
        # Démarre la vérification des entrées
        self.check_entry_status()

    def load_config(self):
        """Charge la configuration."""
        # Charge le thème
        theme_name = self.db.get_setting('theme', 'dark')
        self.current_theme = Theme(theme_name)
        self.setStyleSheet(self.current_theme.get_stylesheet())
        
        # Charge les autres paramètres
        self.start_time = self.db.get_setting('start_time', "09:00")
        self.end_time = self.db.get_setting('end_time', "17:00")
        self.hours_per_day = float(self.db.get_setting('hours_per_day', "8"))
        self.daily_hours = int(self.db.get_setting('daily_hours', '8'))
        
        # Initialise le client Jira
        jira_config = self.db.get_jira_config()
        if jira_config and jira_config.get('jira_base_url') and jira_config.get('jira_email') and jira_config.get('jira_token'):
            self.jira_client = JiraClient(
                base_url=jira_config['jira_base_url'],
                email=jira_config['jira_email'],
                token=jira_config['jira_token']
            )

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
        self.resize(233, 90)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # Définir l'icône de la fenêtre
        window_icon = self.load_svg_icon("calendar-days.svg")
        self.setWindowIcon(window_icon)
        
        # self.setStyleSheet("""\
        #     QMainWindow {
        #         background-color: #1e1e1e;
        #     }
        #     QWidget {
        #         background-color: #1e1e1e;
        #         color: #d0d0d1;
        #     }
        #     QToolButton {
        #         border: none;
        #         padding: 5px;
        #         color: #d0d0d1;
        #     }
        #     QToolButton:hover {
        #         background-color: #333333;
        #         border-radius: 3px;
        #     }
        #     QLabel {
        #         color: #d0d0d1;
        #         font-size: 13px;
        #         background: transparent;
        #     }
        #     QFrame[frameShape="4"] {  /* HLine */
        #         background-color: #333333;
        #         max-height: 1px;
        #         border: none;
        #     }
        # """)

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
        add_button = create_tool_button('plus.svg', "Ajouter une entrée", self.on_add_clicked)
        list_button = create_tool_button('list.svg', "Voir les entrées", self.show_entries_dialog)
        self.sync_button = create_tool_button('refresh.svg', "Synchroniser vers jira", self.show_sync_dialog)
        new_ticket_button = create_tool_button('ticket-plus.svg', "Créer un nouveau ticket", self.show_create_ticket_dialog)
        config_button = create_tool_button('settings.svg', "Configuration", self.show_config_dialog)
        projects_button = create_tool_button('projects.svg', "Projets", self.show_projects_dialog)

        # Met à jour l'état du bouton de synchronisation
        self.update_sync_button_state()

        # Ajout des boutons à la barre d'outils
        toolbar.addWidget(add_button)
        toolbar.addWidget(list_button)
        toolbar.addWidget(self.sync_button)
        toolbar.addWidget(new_ticket_button)
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
        self.current_time_label.setToolTip("Prochain créneau disponible")
        clock_icon.setToolTip("Prochain créneau disponible")
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

        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("")


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
        """Vérifie les alertes et met à jour l'interface en conséquence."""
        try:
            # Récupère le total des minutes pour aujourd'hui
            total_minutes = self.db.get_total_minutes_for_day(datetime.now().date().isoformat())
            
            # Met à jour le total
            self.total_duration = total_minutes
            
            # Vérifie si on est dans les heures de travail
            now = datetime.now().time()
            start_time = datetime.strptime(self.db.get_setting('start_time', '08:30'), '%H:%M').time()
            end_time = datetime.strptime(self.db.get_setting('end_time', '18:00'), '%H:%M').time()
            
            # Si on est en dehors des heures de travail, pas d'alerte
            if now < start_time or now > end_time:
                return
            
            # Vérifie si on a atteint le nombre d'heures requis
            hours_per_day = float(self.db.get_setting('hours_per_day', '7'))
            minutes_per_day = hours_per_day * 60
            
            # Si on a dépassé le nombre d'heures requis, pas d'alerte
            if total_minutes >= minutes_per_day:
                return
            
            # Vérifie l'état des entrées et met à jour la barre de statut
            self.check_entry_status()
                
        except Exception as e:
            print(f"Erreur lors de la vérification des alertes : {str(e)}")
            self.check_entry_status()

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

            # Calcule le prochain créneau disponible
            start_time = datetime.strptime(self.db.get_setting('start_time', '08:30'), '%H:%M').time()
            next_slot = datetime.combine(today, start_time)

            if entries:
                # Trie les entrées par date et heure
                sorted_entries = sorted(entries, key=lambda x: (x['date'], x['time']))
                
                # Pour chaque entrée, met à jour le prochain créneau disponible
                for entry in sorted_entries:
                    entry_time = datetime.strptime(f"{entry['date']} {entry['time']}", "%Y-%m-%d %H:%M")
                    entry_end = entry_time + timedelta(minutes=entry['duration'])
                    
                    # Si l'entrée commence après le créneau actuel, on garde ce créneau
                    if entry_time > next_slot:
                        break
                    
                    # Sinon, le prochain créneau sera après cette entrée
                    next_slot = entry_end

            # Formate l'heure du prochain créneau
            self.current_time_label.setText(next_slot.strftime("%H:%M"))
            self.current_time_label.setToolTip("Prochain créneau disponible")

        except Exception as e:
            print(f"Erreur lors de la mise à jour du résumé : {str(e)}")

    def set_alert_state(self, state):
        """Change l'état d'alerte et met à jour la couleur de la barre de statut."""
        self.alert_state = state
        
        # Couleurs pour chaque état
        colors = {
            "normal": "",  # Style par défaut
            "warning": """
                QStatusBar {
                    background-color: #FF9800;
                    color: white;
                }
                QSizeGrip {
                    background-color: #FF9800;
                }
            """,
            "danger": """
                QStatusBar {
                    background-color: #F44336;
                    color: white;
                }
                QSizeGrip {
                    background-color: #F44336;
                }
            """
        }
        
        messages = {
            "normal": "",
            "warning": "1 heure sans entrée",
            "danger": ">2 heures sans entrée"
        }
        
        # Applique le style et le message
        if state in colors:
            self.status_bar.setStyleSheet(colors[state])
            self.status_bar.showMessage(messages[state])
            
    def check_entry_status(self):
        """Vérifie le temps écoulé depuis la dernière entrée et met à jour l'état d'alerte."""
        try:
            now = datetime.now()
            entries = self.db.get_entries_for_day(now.date())
            
            if not entries:
                self.set_alert_state("danger")
                return
                
            # Trie les entrées par date et heure pour être sûr d'avoir la plus récente
            entries.sort(key=lambda x: (x['date'], x['time']), reverse=True)
            
            # Prend l'entrée la plus récente
            last_entry = entries[0]
            
            # Calcule la date/heure de fin de la dernière entrée
            entry_datetime = datetime.strptime(f"{last_entry['date']} {last_entry['time']}", "%Y-%m-%d %H:%M")
            end_datetime = entry_datetime + timedelta(minutes=last_entry['duration'])

            
            # Calcule la différence entre maintenant et la fin de la dernière entrée
            time_diff = now - end_datetime
            hours_diff = time_diff.total_seconds() / 3600  # Convertit en heures
            
            if hours_diff <= 1:
                # Moins d'une heure : normal
                self.set_alert_state("normal")
            elif hours_diff <= 2:
                # Entre 1 et 2 heures : warning
                self.set_alert_state("warning")
            else:
                # Plus de 2 heures : danger
                self.set_alert_state("danger")
            
        except Exception as e:
            print(f"Erreur lors de la vérification des entrées : {str(e)}")
            self.set_alert_state("normal")
        
        # Vérifie à nouveau dans 5 minutes
        QTimer.singleShot(5 * 60 * 1000, self.check_entry_status)
        
    def on_add_clicked(self):
        """Ouvre la fenêtre de saisie appropriée selon le paramètre."""
        entry_type = self.db.get_setting('entry_screen_type', 'time_only')
        if entry_type == 'time_and_todo':
            self.show_entry_dialog_v2()
        else:
            self.show_entry_dialog()

    def show_entry_dialog(self):
        """Affiche la fenêtre de saisie."""
        if self.entry_dialog is not None:
            self.entry_dialog.close()
        self.entry_dialog = EntryDialog(self, self.db)

        if self.entry_dialog.exec() == QDialog.DialogCode.Accepted:
            # Met à jour last_entry_time avec la nouvelle entrée
            entries = self.db.get_entries_for_day(datetime.now().date())
            if entries:
                last_entry = entries[0]  # La première entrée est la plus récente
                self.last_entry_time = datetime.strptime(f"{last_entry['date']} {last_entry['time']}", "%Y-%m-%d %H:%M")
            self.update_summary()
            self.check_alerts()  # Force la vérification des alertes

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

    def show_entry_dialog_v2(self):
        """Affiche la nouvelle version de la fenêtre de saisie."""
        if not self.entry_dialog or not self.entry_dialog.isVisible():
            self.entry_dialog = EntryDialogV2(self, self.db, self.current_theme)
        self.entry_dialog.show()
        self.entry_dialog.activateWindow()

    def show_create_ticket_dialog(self):
        """Affiche la fenêtre de création de ticket."""
        if not self.jira_client:
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord configurer la connexion Jira")
            return
            
        dialog = CreateTicketDialog(self, self.db, self.jira_client)
        dialog.exec()


def main():
    """Point d'entrée de l'application."""
    app = QApplication(sys.argv)
    window = LogTrackerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
