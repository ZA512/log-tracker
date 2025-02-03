#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QTimeEdit,
    QComboBox, QGroupBox, QFormLayout, QCheckBox
)
from PyQt6.QtCore import QTime
import os
import json
from utils.database import Database
from ui.theme import Theme

class ConfigDialog(QDialog):
    """Fenêtre de configuration pour les paramètres de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.init_ui()
        self.load_config()
        self.resize(400, 500)

    def init_ui(self):
        """Initialise l'interface utilisateur."""
        layout = QVBoxLayout()
        
        # Groupe Paramètres généraux
        general_group = QGroupBox("Paramètres généraux")
        general_layout = QFormLayout()
        
        # Heures de travail
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        general_layout.addRow("Heure de début:", self.start_time)
        
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm")
        general_layout.addRow("Heure de fin:", self.end_time)
        
        self.hours_per_day = QLineEdit()
        self.hours_per_day.setPlaceholderText("8")
        general_layout.addRow("Heures de travail par jour:", self.hours_per_day)
        
        self.use_sequential_time = QCheckBox("Utiliser l'heure séquentielle")
        general_layout.addRow(self.use_sequential_time)
        
        # Sélecteur de thème
        self.theme_combo = QComboBox()
        themes = Theme.get_available_themes()
        for theme_name in themes.keys():
            self.theme_combo.addItem(theme_name)
        current_theme = self.db.get_setting('theme', 'dark')
        index = self.theme_combo.findText(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        general_layout.addRow("Thème:", self.theme_combo)
        
        # Sélecteur du type d'écran de saisie
        self.entry_type_combo = QComboBox()
        self.entry_type_combo.addItem("Saisir du temps", "time_only")
        self.entry_type_combo.addItem("Saisir temps et tâche à faire", "time_and_todo")
        current_entry_type = self.db.get_setting('entry_screen_type', 'time_only')
        index = self.entry_type_combo.findData(current_entry_type)
        if index >= 0:
            self.entry_type_combo.setCurrentIndex(index)
        general_layout.addRow("Type d'écran de saisie:", self.entry_type_combo)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Groupe Jira
        jira_group = QGroupBox("Configuration Jira")
        jira_layout = QFormLayout()
        
        self.jira_url = QLineEdit()
        self.jira_url.setPlaceholderText("https://your-domain.atlassian.net")
        jira_layout.addRow("URL Jira:", self.jira_url)
        
        self.jira_token = QLineEdit()
        self.jira_token.setPlaceholderText("Votre token Jira")
        self.jira_token.setEchoMode(QLineEdit.EchoMode.Password)
        jira_layout.addRow("Token Jira:", self.jira_token)
        
        self.jira_user = QLineEdit()
        self.jira_user.setPlaceholderText("prenom.nom@email.com")
        jira_layout.addRow("Utilisateur Jira:", self.jira_user)
        
        jira_group.setLayout(jira_layout)
        layout.addWidget(jira_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.save_config)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def load_config(self):
        """Charge la configuration depuis la base de données."""
        # Paramètres généraux
        start_time = self.db.get_setting('start_time', '09:00')
        self.start_time.setTime(QTime.fromString(start_time, "HH:mm"))
        
        end_time = self.db.get_setting('end_time', '17:00')
        self.end_time.setTime(QTime.fromString(end_time, "HH:mm"))
        
        hours = self.db.get_setting('hours_per_day', '8')
        self.hours_per_day.setText(hours)
        
        use_sequential = self.db.get_setting('use_sequential_time', '0')
        self.use_sequential_time.setChecked(use_sequential == '1')
        
        # Configuration Jira
        config = self.db.get_jira_config()
        self.jira_url.setText(config.get('jira_base_url', ''))
        self.jira_token.setText(config.get('jira_token', ''))
        self.jira_user.setText(config.get('jira_user', ''))

    def save_config(self):
        """Enregistre la configuration dans la base de données."""
        try:
            # Paramètres généraux
            self.db.save_setting('start_time', self.start_time.time().toString("HH:mm"))
            self.db.save_setting('end_time', self.end_time.time().toString("HH:mm"))
            self.db.save_setting('hours_per_day', self.hours_per_day.text())
            self.db.save_setting('use_sequential_time', '1' if self.use_sequential_time.isChecked() else '0')
            self.db.save_setting('theme', self.theme_combo.currentText())
            self.db.save_setting('entry_screen_type', self.entry_type_combo.currentData())
            
            # Configuration Jira
            self.db.save_setting('jira_base_url', self.jira_url.text())
            self.db.save_setting('jira_token', self.jira_token.text())
            self.db.save_setting('jira_user', self.jira_user.text())
            
            QMessageBox.information(self, "Succès", "Configuration enregistrée avec succès")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {str(e)}")
