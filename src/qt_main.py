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
from PyQt6.QtGui import QFont, QIcon, QPainter, QColor
import os

from utils.database import Database
from utils.autocomplete import AutocompleteLineEdit
from ui.ticket_combo import TicketComboBox
from ui.project_combo import ProjectComboBox
from ui.config_dialog import ConfigDialog
from ui.sync_dialog import SyncDialog
from ui.entry_dialog import EntryDialog
from ui.entries_dialog import EntriesDialog

from PyQt6.QtWidgets import QMainWindow  # Added import statement

class LogTrackerApp(QMainWindow):
    """Fenêtre principale de l'application."""

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.entry_dialog = None
        self.entries_dialog = None
        self.config_dialog = None
        self.sync_dialog = None
        self.setup_ui()
        self.setup_timer()

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
        sync_button = create_tool_button('refresh.svg', "Synchroniser vers jira", self.show_sync_dialog)
        config_button = create_tool_button('settings.svg', "Configuration", self.show_config_dialog)

        # Ajout des boutons à la barre d'outils
        toolbar.addWidget(add_button)
        toolbar.addWidget(list_button)
        toolbar.addWidget(sync_button)
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
        # Crée une nouvelle instance à chaque fois
        self.entry_dialog = EntryDialog(self, self.db)

        if self.entry_dialog.exec() == QDialog.DialogCode.Accepted:
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
        if not self.config_dialog:
            self.config_dialog = ConfigDialog(self)
        self.config_dialog.show()
    
    def show_sync_dialog(self):
        """Affiche la fenêtre de synchronisation."""
        if not self.sync_dialog:
            self.sync_dialog = SyncDialog(self)
        self.sync_dialog.load_entries()  # Rafraîchit à chaque ouverture
        self.sync_dialog.show()
        self.sync_dialog.raise_()

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
