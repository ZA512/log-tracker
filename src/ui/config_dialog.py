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
from utils.ms_graph_client import MSGraphClient

class ConfigDialog(QDialog):
    """Fenêtre de configuration pour les paramètres de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.ms_client = None
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
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Groupe Configuration Jira
        jira_group = QGroupBox("Configuration Jira")
        jira_layout = QFormLayout()
        
        self.jira_url = QLineEdit()
        jira_layout.addRow("URL Jira:", self.jira_url)
        
        self.jira_email = QLineEdit()
        jira_layout.addRow("Email:", self.jira_email)
        
        self.jira_token = QLineEdit()
        self.jira_token.setEchoMode(QLineEdit.EchoMode.Password)
        jira_layout.addRow("Token API:", self.jira_token)
        
        self.token_expiry = QLineEdit()
        self.token_expiry.setPlaceholderText("JJ/MM/AAAA")
        jira_layout.addRow("Date d'expiration du token:", self.token_expiry)
        
        jira_group.setLayout(jira_layout)
        layout.addWidget(jira_group)
        
        # Groupe Configuration Microsoft
        ms_group = QGroupBox("Configuration Microsoft")
        ms_layout = QFormLayout()
        
        self.client_id = QLineEdit()
        ms_layout.addRow("Client ID:", self.client_id)
        
        self.tenant_id = QLineEdit()
        ms_layout.addRow("Tenant ID:", self.tenant_id)
        
        self.ms_token = QLineEdit()
        self.ms_token.setEchoMode(QLineEdit.EchoMode.Password)
        ms_layout.addRow("Token MSAL:", self.ms_token)
        
        self.ms_connect_btn = QPushButton("Se connecter à Microsoft")
        ms_layout.addRow(self.ms_connect_btn)
        
        self.planner_combo = QComboBox()
        self.planner_combo.setEnabled(False)
        ms_layout.addRow("Plan Planner:", self.planner_combo)
        
        ms_group.setLayout(ms_layout)
        layout.addWidget(ms_group)
        
        # Boutons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Enregistrer")
        self.save_button.clicked.connect(self.save_config)
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.setWindowTitle("Configuration")

    def load_config(self):
        """Charge la configuration depuis la base de données."""
        try:
            # Charge depuis la base de données
            start_time = self.db.get_setting('start_time', "08:30")
            self.start_time.setTime(QTime.fromString(start_time, "HH:mm"))
            
            end_time = self.db.get_setting('end_time', "18:00")
            self.end_time.setTime(QTime.fromString(end_time, "HH:mm"))
            
            hours_per_day = self.db.get_setting('hours_per_day', "8")
            self.hours_per_day.setText(hours_per_day)
            
            use_sequential = self.db.get_setting('use_sequential_time', "0")
            self.use_sequential_time.setChecked(use_sequential == "1")
            
            # Paramètres Jira
            self.jira_url.setText(self.db.get_setting('jira_base_url', ''))
            self.jira_email.setText(self.db.get_setting('jira_email', ''))
            self.jira_token.setText(self.db.get_setting('jira_token', ''))
            self.token_expiry.setText(self.db.get_setting('token_expiry', ''))
            
            # Paramètres Microsoft
            self.client_id.setText(self.db.get_setting('ms_client_id', ''))
            self.tenant_id.setText(self.db.get_setting('ms_tenant_id', ''))
            self.ms_token.setText(self.db.get_setting('ms_token', ''))
            
            # Si les IDs sont renseignés, charge les plans
            if self.client_id.text() and self.tenant_id.text():
                self.ms_client = MSGraphClient(self.client_id.text(), self.tenant_id.text())
                plans = self.ms_client.get_plans()
                if plans:
                    self.planner_combo.clear()
                    for plan in plans:
                        display_text = f"{plan['title']} ({plan['group_name']})"
                        self.planner_combo.addItem(display_text, plan['id'])
                    
                    saved_plan_id = self.db.get_setting('ms_plan_id')
                    if saved_plan_id:
                        index = self.planner_combo.findData(saved_plan_id)
                        if index >= 0:
                            self.planner_combo.setCurrentIndex(index)
                    self.planner_combo.setEnabled(True)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement de la configuration : {str(e)}")

    def save_config(self):
        """Enregistre la configuration dans la base de données."""
        try:
            # Enregistre dans la base de données
            self.db.save_setting('start_time', self.start_time.time().toString("HH:mm"))
            self.db.save_setting('end_time', self.end_time.time().toString("HH:mm"))
            self.db.save_setting('hours_per_day', self.hours_per_day.text())
            self.db.save_setting('use_sequential_time', "1" if self.use_sequential_time.isChecked() else "0")
            
            # Paramètres Jira
            self.db.save_setting('jira_base_url', self.jira_url.text())
            self.db.save_setting('jira_email', self.jira_email.text())
            self.db.save_setting('jira_token', self.jira_token.text())
            self.db.save_setting('token_expiry', self.token_expiry.text())
            
            # Paramètres Microsoft
            self.db.save_setting('ms_client_id', self.client_id.text())
            self.db.save_setting('ms_tenant_id', self.tenant_id.text())
            self.db.save_setting('ms_token', self.ms_token.text())
            
            if self.planner_combo.currentData():
                self.db.save_setting('ms_plan_id', self.planner_combo.currentData())
            
            self.accept()
            QMessageBox.information(self, "Succès", "Configuration enregistrée avec succès!")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {str(e)}")
