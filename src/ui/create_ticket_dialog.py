#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QTextEdit,
    QPushButton, QLabel, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt

from .parent_ticket_combo import ParentTicketComboBox

class CreateTicketDialog(QDialog):
    """Fenêtre de création d'un nouveau ticket Jira."""
    
    def __init__(self, parent=None, db=None, jira_client=None):
        super().__init__(parent)
        self.db = db
        self.jira_client = jira_client
        self.setup_ui()
        self.load_paths()
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Créer un nouveau ticket")
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Parent ticket (from jira_paths)
        self.parent_combo = ParentTicketComboBox()
        form_layout.addRow("Ticket parent:", self.parent_combo)
        
        # Title
        self.title_input = QLineEdit()
        form_layout.addRow("Titre:", self.title_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMinimumHeight(150)
        form_layout.addRow("Description:", self.description_input)
        
        # Labels
        self.labels_label = QLabel("Étiquette: security")
        form_layout.addRow(self.labels_label)
        
        # Components (security tag)
        self.components_label = QLabel("Components: Security (10297)")
        form_layout.addRow(self.components_label)
        
        # Programme
        self.program_label = QLabel("Programme: Autre (10057) > Autre (10286)")
        form_layout.addRow(self.program_label)
        
        layout.addLayout(form_layout)
        
        # Create button
        self.create_button = QPushButton("Créer le ticket")
        self.create_button.clicked.connect(self.create_ticket)
        layout.addWidget(self.create_button)
        
        self.setLayout(layout)
    
    def load_paths(self):
        """Charge les chemins depuis jira_paths."""
        try:
            paths = self.db.get_jira_paths()
            self.parent_combo.set_tickets(paths)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des chemins : {str(e)}")
    
    def create_ticket(self):
        """Crée le ticket dans Jira."""
        try:
            if not self.jira_client:
                raise Exception("Client Jira non configuré")
            
            # Récupère le ticket parent
            parent_key = self.parent_combo.get_current_ticket()
            if not parent_key:
                raise Exception("Veuillez sélectionner un ticket parent")
            
            # Récupère les autres champs
            title = self.title_input.text().strip()
            description = self.description_input.toPlainText().strip()
            
            if not title:
                raise Exception("Le titre est obligatoire")
            
            # Crée le ticket avec les champs fixes
            issue = self.jira_client.create_subtask(
                parent_key=parent_key,
                summary=title,
                description=description,
                components=[{"id": "10297"}],  # Security
                programme={"id": "10057"},  # Autre
                sous_programme={"id": "10286"}  # Autre
            )
            
            if issue:
                QMessageBox.information(self, "Succès", f"Ticket créé : {issue['key']}")
                self.accept()
            else:
                raise Exception("Erreur lors de la création du ticket")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du ticket : {str(e)}")
