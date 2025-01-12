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

class EntryDialog(QDialog):
    """Fenêtre de saisie d'une nouvelle entrée."""

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.jira_client = None
        self.setup_jira_client()
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setup_ui()
        self.setup_suggestions()  # Initialise les suggestions
        self.clear_all(init=True)  # Efface tout à l'initialisation
        # Force le focus sur le projet
        QTimer.singleShot(0, lambda: self.project_input.setFocus())

    def setup_jira_client(self):
        """Configure le client Jira avec les paramètres de la base de données."""
        try:
            base_url = self.db.get_setting('jira_base_url')
            token = self.db.get_setting('jira_token')
            email = self.db.get_setting('jira_email')
            
            if base_url and token and email:
                from utils.jira_client import JiraClient
                self.jira_client = JiraClient(base_url, token, email)
            else:
                print("Configuration Jira incomplète - URL, email ou token manquant")
        except Exception as e:
            print(f"Erreur lors de la configuration du client Jira : {str(e)}")

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Ajouter une entrée")
        self.setModal(True)
        self.resize(400, 350)  # Un peu plus haut pour les boutons de raccourci

        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Date et heure
        date_time_layout = QHBoxLayout()
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime.currentTime())
        self.time_input.setDisplayFormat("HH:mm")
        
        date_time_layout.addWidget(self.date_input)
        date_time_layout.addWidget(self.time_input)
        form_layout.addRow("Date et heure:", date_time_layout)

        # Projet
        self.project_input = ProjectComboBox()
        self.project_input.projectChanged.connect(self.on_project_changed)
        form_layout.addRow("Projet:", self.project_input)

        # Ticket
        self.ticket_input = TicketComboBox()
        self.ticket_input.ticketChanged.connect(self.on_ticket_selected)
        form_layout.addRow("Ticket:", self.ticket_input)

        # Titre du ticket
        self.ticket_title = QLineEdit()
        self.ticket_title.setPlaceholderText("Le titre sera récupéré automatiquement depuis Jira")
        self.ticket_title.focusInEvent = self.on_title_focus
        form_layout.addRow("Titre:", self.ticket_title)

        # Description
        self.description_input = QTextEdit()
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
        self.duration_input.setMaximum(480)  # 8 heures
        self.duration_input.setValue(60)  # 1 heure par défaut
        self.duration_input.setSuffix(" minutes")
        
        spinbox_layout.addWidget(self.duration_input)
        spinbox_layout.addStretch()
        
        duration_layout.addLayout(spinbox_layout)
        
        # Ligne avec les boutons de raccourcis
        shortcuts_layout = QHBoxLayout()
        shortcuts_layout.setSpacing(5)
        
        # Fonction pour créer un bouton de raccourci
        def create_shortcut_button(text, minutes):
            button = QPushButton(text)
            button.clicked.connect(lambda: self.duration_input.setValue(minutes))
            button.setFixedWidth(40)
            button.setAutoDefault(False)  # Empêche le bouton d'être sélectionné par défaut
            button.setDefault(False)      # Empêche le bouton d'être le bouton par défaut
            return button
        
        # Création des boutons de raccourcis
        durations = [
            ("15m", 15), ("30m", 30), ("1h", 60), ("2h", 120),
            ("3h", 180), ("4h", 240), ("5h", 300), ("6h", 360),
            ("7h", 420), ("8h", 480)
        ]
        
        for text, minutes in durations:
            shortcuts_layout.addWidget(create_shortcut_button(text, minutes))
        
        duration_layout.addLayout(shortcuts_layout)
        form_layout.addRow("Durée:", duration_widget)

        main_layout.addLayout(form_layout)

        # Boutons
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Sauvegarder")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        clear_button = QPushButton("Effacer")
        clear_button.clicked.connect(self.clear_all)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(clear_button)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def clear_all(self, init=False):
        """Efface tous les champs et remet les valeurs par défaut."""
        # Remet la date et l'heure actuelles
        self.date_input.setDate(QDate.currentDate())
        self.time_input.setTime(QTime.currentTime())
        
        # Efface les autres champs
        self.project_input.clear()
        self.ticket_input.clear()
        self.ticket_title.clear()
        self.description_input.clear()
        self.duration_input.setValue(60)
        
        # Recharge les projets pour l'autocomplétion seulement à l'initialisation
        if init:
            self.setup_suggestions()
        
        # Remet le focus sur le projet
        self.project_input.setFocus()

    def setup_suggestions(self):
        """Initialise les suggestions pour les projets."""
        try:
            projects = self.db.get_project_suggestions()
            self.project_input.set_projects(projects)
        except Exception as e:
            print(f"Erreur lors de l'initialisation des suggestions : {str(e)}")

    def on_project_changed(self, project_name):
        """Appelé lorsque le projet change."""
        if isinstance(project_name, str):
            project_text = project_name
        else:
            project_text = project_name.text() if project_name else ""

        # Récupère la liste des tickets pour ce projet
        project = self.db.get_project_by_name(project_text)
        if project:
            tickets = self.db.get_project_tickets(project['id'])
            self.ticket_input.set_tickets(tickets)
        else:
            self.ticket_input.set_tickets([])

    def on_ticket_selected(self, ticket_number):
        """Appelé lorsqu'un ticket est sélectionné."""
        if not ticket_number:
            self.ticket_title.clear()
            return

        if isinstance(ticket_number, str):
            ticket_text = ticket_number
        else:
            ticket_text = ticket_number.text() if ticket_number else ""

        if not ticket_text:
            self.ticket_title.clear()
            return

        # Récupère le projet actuel
        project_name = self.project_input.text()
        if not project_name:
            return

        # Récupère l'ID du projet
        project = self.db.get_project_by_name(project_name)
        if not project:
            return

        # Récupère les informations du ticket
        ticket_info = self.db.get_ticket_info(project['id'], ticket_text)
        if ticket_info:
            # Si le ticket existe mais n'a pas de titre, on essaie de le récupérer depuis Jira
            if not ticket_info[2]:  # ticket_info[2] est le titre
                self.fetch_ticket_title_from_jira(ticket_text)
            else:
                self.ticket_title.setText(ticket_info[2])
        else:
            # Si le ticket n'existe pas encore, on essaie de récupérer son titre depuis Jira
            self.fetch_ticket_title_from_jira(ticket_text)

    def fetch_ticket_title_from_jira(self, ticket_number):
        """Récupère le titre du ticket depuis Jira."""
        if not self.jira_client:
            print("Client Jira non configuré")
            return

        try:
            issue = self.jira_client.get_issue_details(ticket_number)
            if issue and issue.get('summary'):
                self.ticket_title.setText(issue['summary'])
                
                # Sauvegarde le titre dans la base de données
                project_name = self.project_input.text()
                if project_name:
                    project = self.db.get_project_by_name(project_name)
                    if project:
                        ticket_info = self.db.get_ticket_info(project['id'], ticket_number)
                        if ticket_info:
                            self.db.update_ticket_title(ticket_info[0], issue['summary'])
                        else:
                            self.db.add_ticket(project['id'], ticket_number, issue['summary'])
        except Exception as e:
            print(f"Erreur lors de la récupération du titre du ticket {ticket_number}: {str(e)}")

    def on_title_focus(self, event):
        """Appelé lorsque le champ titre reçoit le focus."""
        if not self.ticket_title.text().strip():  # Si le titre est vide
            ticket_text = self.ticket_input.text()
            if ticket_text:
                self.fetch_ticket_title_from_jira(ticket_text)
        # Appelle l'événement focusIn par défaut
        QLineEdit.focusInEvent(self.ticket_title, event)

    def accept(self):
        """Appelé lorsque l'utilisateur valide le dialogue."""
        project_name = self.project_input.text()
        ticket_number = self.ticket_input.text()
        description = self.description_input.toPlainText()
        duration = self.duration_input.value()
        ticket_title = self.ticket_title.text()
        date = self.date_input.date().toString("yyyy-MM-dd")
        time = self.time_input.time().toString("HH:mm")

        if not description:
            QMessageBox.warning(self, "Erreur", "La description est obligatoire.")
            return

        try:
            # Récupère ou crée le projet
            project = self.db.get_project_by_name(project_name)
            if project_name and not project:
                project_id = self.db.add_project(project_name)
            else:
                project_id = project['id'] if project else None

            # Récupère ou crée le ticket
            ticket_id = None
            if project_id and ticket_number:
                ticket_info = self.db.get_ticket_info(project_id, ticket_number)
                if ticket_info:
                    ticket_id = ticket_info[0]
                    # Met à jour le titre si nécessaire
                    if ticket_title != ticket_info[2]:
                        self.db.update_ticket_title(ticket_id, ticket_title)
                else:
                    ticket_id = self.db.add_ticket(project_id, ticket_number, ticket_title)

            # Ajoute l'entrée
            self.db.add_entry(
                description=description,
                project_id=project_id,
                ticket_id=ticket_id,
                duration=duration,
                ticket_title=ticket_title,
                date=date,
                time=time
            )

            super().accept()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {str(e)}")


class EntriesDialog(QDialog):
    """Fenêtre d'affichage des entrées."""

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setup_ui()
        self.update_entries_view()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
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
        self.tree.setHeaderLabels(["Projet", "Ticket", "Durée", "Description", "Date", "Heure", ""])  # Colonne vide pour le retour à la ligne
        self.tree.setColumnWidth(0, 150)  # Projet
        self.tree.setColumnWidth(1, 100)  # Ticket
        self.tree.setColumnWidth(2, 80)   # Durée
        self.tree.setColumnWidth(3, 400)  # Description
        self.tree.setColumnWidth(4, 100)  # Date
        self.tree.setColumnWidth(5, 60)   # Heure
        self.tree.setColumnWidth(6, 10)   # Colonne vide
        self.tree.setWordWrap(True)
        layout.addWidget(self.tree)

        self.setLayout(layout)

        # Connexion des signaux
        self.period_day.toggled.connect(self.update_entries_view)
        self.period_8days.toggled.connect(lambda checked: self.view_group.setVisible(checked))
        self.view_by_day.toggled.connect(self.update_entries_view)
        self.view_by_project.toggled.connect(self.update_entries_view)

    def update_entries_view(self):
        """Met à jour l'affichage des entrées."""
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
                        
                        # Ticket en bleu
                        ticket = entry.get('ticket_number', '')
                        entry_item.setText(1, ticket)
                        if ticket:
                            entry_item.setForeground(1, QColor("#64b5f6"))
                        
                        # Durée en vert
                        duration = entry.get('duration', 0)
                        entry_item.setText(2, f"{duration}m")
                        entry_item.setForeground(2, QColor("#81c784"))
                        
                        entry_item.setText(3, entry.get('description', ''))
                        entry_item.setText(4, entry.get('date', ''))
                        entry_item.setText(5, entry.get('time', ''))

                self.tree.expandAll()

            elif self.view_by_day.isChecked():
                # Vue sur 8 jours chronologique
                entries = self.db.get_entries_by_date_range(start_date, end_date)
                if not entries:
                    return

                # Organise les entrées par date
                entries_by_date = {}
                for entry in entries:
                    entry_timestamp = datetime.strptime(f"{entry.get('date', '')} {entry.get('time', '')}", "%Y-%m-%d %H:%M")
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
                        entry_timestamp = datetime.strptime(f"{entry.get('date', '')} {entry.get('time', '')}", "%Y-%m-%d %H:%M")
                        entry_item = QTreeWidgetItem(date_item)
                        entry_item.setText(0, entry.get('project_name', ''))
                        
                        # Ticket en bleu
                        ticket = entry.get('ticket_number', '')
                        entry_item.setText(1, ticket)
                        if ticket:
                            entry_item.setForeground(1, QColor("#64b5f6"))
                        
                        # Durée en vert
                        duration = entry.get('duration', 0)
                        entry_item.setText(2, f"{duration}m")
                        entry_item.setForeground(2, QColor("#81c784"))
                        
                        entry_item.setText(3, f"{entry_timestamp.strftime('%H:%M')} - {entry.get('description', '')}")
                        entry_item.setText(4, entry.get('date', ''))
                        entry_item.setText(5, entry.get('time', ''))

                self.tree.expandAll()

            else:  # Vue par projet sur 8 jours
                entries_by_project = self.db.get_entries_by_project(start_date, end_date)
                if not entries_by_project:
                    return

                for project_name, entries in entries_by_project.items():
                    project_item = QTreeWidgetItem(self.tree)
                    project_item.setText(0, project_name or 'Sans projet')
                    total_duration = sum(entry.get('duration', 0) for entry in entries)
                    project_item.setText(2, f"{total_duration}m")

                    for entry in entries:
                        entry_timestamp = datetime.strptime(f"{entry.get('date', '')} {entry.get('time', '')}", "%Y-%m-%d %H:%M")
                        entry_item = QTreeWidgetItem(project_item)
                        entry_item.setText(0, "")  # Projet déjà affiché dans le parent
                        
                        # Ticket en bleu
                        ticket = entry.get('ticket_number', '')
                        entry_item.setText(1, ticket)
                        if ticket:
                            entry_item.setForeground(1, QColor("#64b5f6"))
                        
                        # Durée en vert
                        duration = entry.get('duration', 0)
                        entry_item.setText(2, f"{duration}m")
                        entry_item.setForeground(2, QColor("#81c784"))
                        
                        entry_item.setText(3, f"{entry_timestamp.strftime('%d/%m %H:%M')} - {entry.get('description', '')}")
                        entry_item.setText(4, entry.get('date', ''))
                        entry_item.setText(5, entry.get('time', ''))

                self.tree.expandAll()

        except Exception as e:
            print(f"Erreur lors de la mise à jour de la vue : {str(e)}")
            import traceback
            traceback.print_exc()


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
        if self.entries_dialog is None:
            self.entries_dialog = EntriesDialog(self, self.db)
        self.entries_dialog.show()

    def show_config_dialog(self):
        """Affiche la fenêtre de configuration."""
        if not self.config_dialog:
            self.config_dialog = ConfigDialog(self)
        self.config_dialog.show()
    
    def show_sync_dialog(self):
        """Affiche la fenêtre de synchronisation."""
        if not self.sync_dialog:
            self.sync_dialog = SyncDialog(self)
        self.sync_dialog.show()

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
