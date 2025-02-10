#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timedelta, date
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QFrame, QSpinBox, QComboBox, QRadioButton, QButtonGroup, QGroupBox,
    QSplitter, QDialog, QFormLayout, QStyle, QToolButton, QDialogButtonBox, QMessageBox,
    QDateEdit, QTimeEdit, QSlider, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize, QDate, QTime
from PyQt6.QtGui import QFont, QIcon, QPainter, QColor
import os

from utils.database import Database
from utils.autocomplete import AutocompleteLineEdit
from ui.ticket_combo import TicketComboBox
from ui.project_combo import ProjectComboBox
from ui.ticket_search_dialog import TicketSearchDialog
from ui.create_ticket_dialog import CreateTicketDialog

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

    @property
    def time_increment(self):
        """Récupère l'incrément de temps depuis la configuration."""
        return int(self.db.get_setting('time_increment', '5'))

    def setup_jira_client(self):
        """Configure le client Jira avec les paramètres de la base de données."""
        try:
            base_url = self.db.get_setting('jira_base_url')
            token = self.db.get_setting('jira_token')
            email = self.db.get_setting('jira_email')
            
            if base_url and token and email:
                from utils.jira_client import JiraClient
                self.jira_client = JiraClient(base_url, token, email)
        except Exception as e:
            pass

    def update_remaining_time(self, info_button):
        """Met à jour le tooltip avec le temps restant à saisir."""
        try:
            # Récupère le nombre d'heures par jour depuis les paramètres
            daily_hours = int(self.db.get_setting('daily_hours', '8'))
            total_minutes = daily_hours * 60
            
            # Récupère la date sélectionnée
            selected_date = self.date_input.date().toString('yyyy-MM-dd')
            
            # Calcule le temps déjà saisi
            used_minutes = self.db.get_total_minutes_for_day(selected_date)
            
            # Calcule le temps restant
            remaining_minutes = total_minutes - used_minutes
            
            # Formate le message
            if remaining_minutes > 0:
                message = f"Temps restant à placer sur la journée : {remaining_minutes} minutes"
            else:
                surplus = abs(remaining_minutes)
                message = f"Dépassement du temps journalier de {surplus} minutes"
            
            # Met à jour le tooltip
            info_button.setToolTip(message)
            
        except Exception as e:
            info_button.setToolTip(f"Erreur lors du calcul du temps restant : {str(e)}")

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Ajouter une entrée")
        self.setModal(True)
        self.resize(400, 350)  # Un peu plus haut pour les boutons de raccourci

        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)  # Permet aux widgets de la colonne des champs de s'étendre sur toute la largeur

        # Date et heure
        date_time_layout = QHBoxLayout()
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        
        self.time_input = QTimeEdit()
        if self.db.get_setting('use_sequential_time', '0') == '1':
            sequential_time = self.db.get_sequential_time(self.date_input.date().toString("yyyy-MM-dd"))
            self.time_input.setTime(QTime.fromString(sequential_time, "HH:mm"))
        else:
            self.time_input.setTime(QTime.currentTime())
        self.time_input.setDisplayFormat("HH:mm")
        
        date_time_layout.addWidget(self.date_input)
        date_time_layout.addWidget(self.time_input)
        form_layout.addRow("Date et heure:", date_time_layout)

        # Projet
        self.project_input = ProjectComboBox()
        self.project_input.projectChanged.connect(self.on_project_changed)
        form_layout.addRow("Projet:", self.project_input)

        # Ticket avec bouton de recherche
        ticket_layout = QHBoxLayout()
        self.ticket_input = TicketComboBox()
        self.ticket_input.ticketChanged.connect(self.on_ticket_selected)
        ticket_layout.addWidget(self.ticket_input)
        
        search_button = QPushButton("Rechercher")
        search_button.clicked.connect(self._open_ticket_search)
        search_button.setFixedWidth(100)
        ticket_layout.addWidget(search_button)
        
        form_layout.addRow("Ticket:", ticket_layout)

        # Titre du ticket
        self.ticket_title = QLineEdit()
        self.ticket_title.setPlaceholderText("Le titre sera récupéré automatiquement depuis Jira")
        self.ticket_title.focusInEvent = self.on_title_focus
        form_layout.addRow("Titre:", self.ticket_title)

        # Fait
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(75)  # Hauteur réduite
        form_layout.addRow("Fait:", self.description_input)

        # Durée avec spinbox aligné avec les autres champs
        duration_top_layout = QHBoxLayout()
        
        # SpinBox pour la durée en minutes (aligné avec les autres champs)
        self.duration_input = QSpinBox()
        self.duration_input.setMinimum(self.time_increment)
        self.duration_input.setMaximum(480)
        self.duration_input.setValue(60)  # 1 heure par défaut
        self.duration_input.setSuffix(" minutes")
        self.duration_input.valueChanged.connect(self.on_spinbox_changed)
        duration_top_layout.addWidget(self.duration_input)

        # Icône d'information pour le temps restant
        info_button = QToolButton()
        info_button.setIcon(QIcon("src/resources/info.svg"))
        info_button.setToolTip("Chargement...")
        duration_top_layout.addWidget(info_button)
        duration_top_layout.addStretch()
        
        # Créer un label temporaire pour mesurer la largeur
        temp_label = QLabel("Durée:")
        label_width = temp_label.sizeHint().width()
        
        form_layout.addRow("Durée:", duration_top_layout)

        # Label pour afficher le temps au format HH:MM
        duration_label_container = QWidget()
        duration_label_layout = QHBoxLayout(duration_label_container)
        duration_label_layout.setContentsMargins(0, 0, 0, 0)
        self.duration_label = QLabel("01h00")  # Valeur initiale 60 minutes
        duration_label_layout.addWidget(self.duration_label)
        duration_label_layout.addStretch()

        # Container pour le slider
        slider_container = QWidget()
        slider_layout = QHBoxLayout(slider_container)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        
        # Slider pour la durée
        self.duration_slider = QSlider(Qt.Orientation.Horizontal)
        self.duration_slider.setMinimum(self.time_increment)
        self.duration_slider.setMaximum(480)
        self.duration_slider.setValue(60)  # 1 heure par défaut
        self.duration_slider.setPageStep(30)
        self.duration_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.duration_slider.valueChanged.connect(self.on_duration_changed)
        self.duration_slider.sliderReleased.connect(self.on_slider_released)
        slider_layout.addWidget(self.duration_slider)
        
        slider_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_layout.addRow(duration_label_container, slider_container)
        
        # Mise à jour du tooltip quand la date change
        self.date_input.dateChanged.connect(lambda: self.update_remaining_time(info_button))
        
        # Mise à jour initiale du tooltip
        QTimer.singleShot(0, lambda: self.update_remaining_time(info_button))
        
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
        """Efface tous les champs."""
        # Remet la date et l'heure actuelles
        self.date_input.setDate(QDate.currentDate())
        if self.db.get_setting('use_sequential_time', '0') == '1':
            sequential_time = self.db.get_sequential_time(self.date_input.date().toString("yyyy-MM-dd"))
            self.time_input.setTime(QTime.fromString(sequential_time, "HH:mm"))
        else:
            self.time_input.setTime(QTime.currentTime())
        
        # Efface les autres champs
        self.project_input.clear()
        self.ticket_input.clear()
        self.ticket_title.clear()
        self.description_input.clear()
        self.duration_slider.setValue(60)  # 1 heure par défaut
        self.duration_input.setValue(60)  # 1 heure par défaut
        
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
        """Appelé lorsque le projet sélectionné change."""
        if not project_name:
            self.ticket_input.set_tickets([])
            return

        # Récupère l'ID du projet
        project = self.db.get_project_by_name(project_name)
        if not project:
            return

        # Récupère les tickets du projet
        tickets = self.db.get_project_tickets(project['id'])
        if tickets:
            # Met à jour la liste des tickets
            self.ticket_input.set_tickets(tickets)
            # Sélectionne le premier ticket mais sans déclencher la recherche du titre
            first_ticket = tickets[0]['ticket_number']
            self.ticket_input.setText(first_ticket)
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
            # Si le ticket existe, on utilise son titre stocké
            if ticket_info[2]:  # ticket_info[2] est le titre
                self.ticket_title.setText(ticket_info[2])
            # Sinon on ne fait rien, la recherche se fera quand l'utilisateur modifiera le ticket
        else:
            # Si le ticket n'existe pas encore, on ne fait rien, la recherche se fera quand l'utilisateur modifiera le ticket
            pass

    def fetch_ticket_title_from_jira(self, ticket_number):
        """Récupère le titre du ticket depuis Jira"""
        if not self.jira_client:
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
        duration = self.duration_slider.value()
        ticket_title = self.ticket_title.text()
        date = self.date_input.date().toString("yyyy-MM-dd")
        time = self.time_input.time().toString("HH:mm")

        if not description:
            QMessageBox.warning(self, "Erreur", "La description est obligatoire.")
            return

        if not project_name:
            QMessageBox.warning(self, "Erreur", "Le projet est obligatoire.")
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
                # Vérifie si le ticket existe déjà dans le projet
                existing_tickets = self.db.get_project_tickets(project_id, include_inactive=True)
                ticket_exists = any(t['ticket_number'] == ticket_number for t in existing_tickets)
                
                if not ticket_exists:
                    # Nouveau ticket, on le crée
                    ticket_id = self.db.add_ticket(project_id, ticket_number, ticket_title)
                else:
                    # Le ticket existe déjà, on récupère ses infos
                    ticket_info = self.db.get_ticket_info(project_id, ticket_number)
                    if ticket_info:
                        ticket_id = ticket_info[0]
                        # Met à jour le titre si nécessaire
                        if ticket_title != ticket_info[2]:
                            self.db.update_ticket_title(ticket_id, ticket_title)

            # Ajoute l'entrée
            self.db.add_entry(
                description=description,
                project_id=project_id,
                ticket_id=ticket_id,
                ticket_title=ticket_title,
                duration=duration,
                date=date,
                time=time
            )

            super().accept()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {str(e)}")

    def _open_ticket_search(self):
        """Ouvre la fenêtre de recherche de tickets."""
        dialog = TicketSearchDialog(self, self.db)
        dialog.ticketSelected.connect(self._on_search_ticket_selected)
        dialog.exec()
    
    def _on_search_ticket_selected(self, ticket_number, title):
        """Appelé quand un ticket est sélectionné dans la recherche."""
        self.ticket_input.combo.setEditText(ticket_number)
        self.ticket_title.setText(title)

    def _open_create_ticket(self):
        """Ouvre la fenêtre de création de ticket."""
        dialog = CreateTicketDialog(self, self.db, self.jira_client)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Le ticket a été créé avec succès, on pourrait rafraîchir la liste des tickets ici si nécessaire
            pass

    def on_duration_changed(self):
        """Appelé lorsque la valeur du slider change."""
        duration = self.duration_slider.value()
        hours = duration // 60
        minutes = duration % 60
        self.duration_label.setText(f"{hours:02d}h{minutes:02d}")
        self.duration_input.setValue(duration)

    def on_slider_released(self):
        """Appelé lorsque le slider est relâché pour aligner sur l'incrément."""
        current_value = self.duration_slider.value()
        # Arrondir à l'incrément le plus proche
        adjusted_value = round(current_value / self.time_increment) * self.time_increment
        self.duration_slider.setValue(adjusted_value)

    def on_spinbox_changed(self):
        """Appelé lorsque la valeur du spinbox change."""
        duration = self.duration_input.value()
        # Arrondir à l'incrément le plus proche
        adjusted_value = round(duration / self.time_increment) * self.time_increment
        if adjusted_value != duration:
            self.duration_input.setValue(adjusted_value)
            return
        self.duration_slider.setValue(adjusted_value)
        hours = adjusted_value // 60
        minutes = adjusted_value % 60
        self.duration_label.setText(f"{hours:02d}h{minutes:02d}")
