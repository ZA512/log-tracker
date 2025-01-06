#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QDateEdit, QLabel
)
from PyQt6.QtCore import Qt, QDate
import json
import os

class ConfigDialog(QDialog):
    """Fenêtre de configuration pour les paramètres de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Configuration")
        self.setModal(True)
        self.resize(400, 200)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Champ pour le token Jira
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Token Jira:", self.token_input)

        # Champ pour la date d'expiration
        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDate(QDate.currentDate().addMonths(1))  # Par défaut : date actuelle + 1 mois
        form_layout.addRow("Date d'expiration:", self.expiry_date)

        # Message d'avertissement pour le token
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: red;")
        form_layout.addRow("", self.warning_label)

        layout.addLayout(form_layout)

        # Boutons
        button_layout = QVBoxLayout()
        save_button = QPushButton("Sauvegarder")
        save_button.clicked.connect(self.save_config)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

    def load_config(self):
        """Charge la configuration depuis le fichier."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.token_input.setText(config.get('jira_token', ''))
                    expiry_date = QDate.fromString(config.get('token_expiry', ''), Qt.DateFormat.ISODate)
                    if expiry_date.isValid():
                        self.expiry_date.setDate(expiry_date)
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration : {e}")

    def save_config(self):
        """Sauvegarde la configuration dans le fichier."""
        config = {
            'jira_token': self.token_input.text(),
            'token_expiry': self.expiry_date.date().toString(Qt.DateFormat.ISODate)
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            self.accept()
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration : {e}")
            self.warning_label.setText(f"Erreur lors de la sauvegarde : {str(e)}")
