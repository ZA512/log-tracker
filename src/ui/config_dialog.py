#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
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
        self.resize(400, 200)

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
        """Charge la configuration depuis le fichier et la base de données."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.jira_token_input.setText(config.get('jira_token', ''))
                    expiry_date = QDate.fromString(config.get('token_expiry', ''), Qt.DateFormat.ISODate)
                    if expiry_date.isValid():
                        self.token_expiry_input.setDate(expiry_date)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement de la configuration : {str(e)}")

        self.jira_url_input.setText(self.db.get_setting('jira_base_url', ''))
        self.jira_email_input.setText(self.db.get_setting('jira_email', ''))

    def save_config(self):
        """Sauvegarde la configuration dans le fichier et la base de données."""
        try:
            jira_url = self.jira_url_input.text().strip()
            jira_email = self.jira_email_input.text().strip()
            jira_token = self.jira_token_input.text().strip()
            token_expiry = self.token_expiry_input.date().toString(Qt.DateFormat.ISODate)

            # Validation basique
            if not jira_email or '@' not in jira_email:
                QMessageBox.warning(self, "Erreur", "Veuillez entrer une adresse email valide")
                return

            # Sauvegarde
            config = {
                'jira_token': jira_token,
                'token_expiry': token_expiry
            }

            with open(self.config_file, 'w') as f:
                json.dump(config, f)

            self.db.save_setting('jira_base_url', jira_url)
            self.db.save_setting('jira_email', jira_email)
            self.db.save_setting('jira_token', jira_token)

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")
