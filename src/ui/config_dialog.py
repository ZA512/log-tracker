#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QDateEdit,
    QTimeEdit, QComboBox
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QIntValidator
from utils.database import Database
import json
import os

class ConfigDialog(QDialog):
    """Fenêtre de configuration pour les paramètres de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Configuration")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout()

        # URL Jira
        jira_url_layout = QHBoxLayout()
        jira_url_label = QLabel("URL Jira:")
        self.jira_url_input = QLineEdit()
        self.jira_url_input.setPlaceholderText("your-domain.atlassian.net")
        jira_url_layout.addWidget(jira_url_label)
        jira_url_layout.addWidget(self.jira_url_input)
        layout.addLayout(jira_url_layout)

        # Email Jira
        jira_email_layout = QHBoxLayout()
        jira_email_label = QLabel("Email Jira:")
        self.jira_email_input = QLineEdit()
        self.jira_email_input.setPlaceholderText("votre.email@domaine.com")
        jira_email_layout.addWidget(jira_email_label)
        jira_email_layout.addWidget(self.jira_email_input)
        layout.addLayout(jira_email_layout)

        # Token Jira
        jira_token_layout = QHBoxLayout()
        jira_token_label = QLabel("Token Jira:")
        self.jira_token_input = QLineEdit()
        self.jira_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        jira_token_layout.addWidget(jira_token_label)
        jira_token_layout.addWidget(self.jira_token_input)
        layout.addLayout(jira_token_layout)

        # Date d'expiration du token
        token_expiry_layout = QHBoxLayout()
        token_expiry_label = QLabel("Date d'expiration du token:")
        self.token_expiry_input = QDateEdit()
        self.token_expiry_input.setCalendarPopup(True)
        token_expiry_layout.addWidget(token_expiry_label)
        token_expiry_layout.addWidget(self.token_expiry_input)
        layout.addLayout(token_expiry_layout)

        # Heure de début de journée
        start_time_layout = QHBoxLayout()
        start_time_label = QLabel("Heure de début de journée:")
        self.start_time_input = QTimeEdit()
        self.start_time_input.setDisplayFormat("HH:mm")
        self.start_time_input.setTime(QTime(8, 0))  # 08:00 par défaut
        start_time_layout.addWidget(start_time_label)
        start_time_layout.addWidget(self.start_time_input)
        layout.addLayout(start_time_layout)

        # Heure de fin de journée
        end_time_layout = QHBoxLayout()
        end_time_label = QLabel("Heure de fin de journée:")
        self.end_time_input = QTimeEdit()
        self.end_time_input.setDisplayFormat("HH:mm")
        self.end_time_input.setTime(QTime(18, 0))  # 18:00 par défaut
        end_time_layout.addWidget(end_time_label)
        end_time_layout.addWidget(self.end_time_input)
        layout.addLayout(end_time_layout)

        # Heures par jour
        daily_hours_layout = QHBoxLayout()
        daily_hours_label = QLabel("Heures de travail par jour:")
        self.daily_hours_input = QLineEdit()
        self.daily_hours_input.setPlaceholderText("8")
        # Accepter uniquement les nombres
        self.daily_hours_input.setValidator(QIntValidator(1, 24))
        daily_hours_layout.addWidget(daily_hours_label)
        daily_hours_layout.addWidget(self.daily_hours_input)
        layout.addLayout(daily_hours_layout)

        # Mode de calcul de l'heure
        time_mode_layout = QHBoxLayout()
        time_mode_label = QLabel("Mode de calcul de l'heure:")
        self.time_mode_input = QComboBox()
        self.time_mode_input.addItem("Heure actuelle", "0")
        self.time_mode_input.addItem("Heure séquentielle", "1")
        time_mode_layout.addWidget(time_mode_label)
        time_mode_layout.addWidget(self.time_mode_input)
        layout.addLayout(time_mode_layout)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Sauvegarder")
        save_button.clicked.connect(self.save_config)
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def load_config(self):
        """Charge la configuration depuis la base de données."""
        try:
            # Charge les paramètres Jira
            self.jira_url_input.setText(self.db.get_setting('jira_base_url', ''))
            self.jira_email_input.setText(self.db.get_setting('jira_email', ''))
            self.jira_token_input.setText(self.db.get_setting('jira_token', ''))
            
            # Charge la date d'expiration
            expiry_date = QDate.fromString(self.db.get_setting('token_expiry', ''), Qt.DateFormat.ISODate)
            if expiry_date.isValid():
                self.token_expiry_input.setDate(expiry_date)
            
            # Charge les heures de début et fin
            start_time = QTime.fromString(self.db.get_setting('start_time', '08:00'), "HH:mm")
            if start_time.isValid():
                self.start_time_input.setTime(start_time)
                
            end_time = QTime.fromString(self.db.get_setting('end_time', '18:00'), "HH:mm")
            if end_time.isValid():
                self.end_time_input.setTime(end_time)
            
            # Charge les heures par jour
            self.daily_hours_input.setText(self.db.get_setting('daily_hours', '8'))
            
            # Charge le mode de calcul de l'heure
            use_sequential = self.db.get_setting('use_sequential_time', '0')
            index = self.time_mode_input.findData(use_sequential)
            if index >= 0:
                self.time_mode_input.setCurrentIndex(index)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement de la configuration : {str(e)}")

    def save_config(self):
        """Sauvegarde la configuration dans la base de données."""
        try:
            # Validation des heures par jour
            daily_hours = self.daily_hours_input.text().strip() or '8'
            try:
                hours = int(daily_hours)
                if hours < 1 or hours > 24:
                    raise ValueError("Les heures doivent être entre 1 et 24")
            except ValueError as e:
                QMessageBox.critical(self, "Erreur", f"Heures invalides : {str(e)}")
                return

            # Sauvegarde les paramètres Jira
            self.db.save_setting('jira_base_url', self.jira_url_input.text().strip())
            self.db.save_setting('jira_email', self.jira_email_input.text().strip())
            self.db.save_setting('jira_token', self.jira_token_input.text().strip())
            
            # Sauvegarde la date d'expiration
            self.db.save_setting('token_expiry', self.token_expiry_input.date().toString(Qt.DateFormat.ISODate))
            
            # Sauvegarde les heures de début et fin
            self.db.save_setting('start_time', self.start_time_input.time().toString("HH:mm"))
            self.db.save_setting('end_time', self.end_time_input.time().toString("HH:mm"))
            
            # Sauvegarde les heures par jour
            self.db.save_setting('daily_hours', daily_hours)
            
            # Sauvegarde le mode de calcul de l'heure
            self.db.save_setting('use_sequential_time', self.time_mode_input.currentData())

            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")
