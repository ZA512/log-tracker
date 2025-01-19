#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QCheckBox, QLabel, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class ProjectsDialog(QDialog):
    """Fenêtre de gestion des projets et tickets."""
    
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Gestion des projets et tickets")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Arbre des projets et tickets
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Nom", "Actif"])
        self.tree.setColumnWidth(0, 600)  # Colonne nom plus large
        layout.addWidget(self.tree)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        # Bouton pour afficher/masquer les éléments inactifs
        self.show_inactive = QCheckBox("Afficher les éléments inactifs")
        self.show_inactive.stateChanged.connect(self.load_data)
        buttons_layout.addWidget(self.show_inactive)
        
        buttons_layout.addStretch()
        
        self.close_button = QPushButton("Fermer")
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
    def load_data(self):
        """Charge les projets et tickets dans l'arbre."""
        self.tree.clear()
        
        # Récupère tous les projets avec leurs tickets
        projects = self.db.get_all_projects(include_inactive=self.show_inactive.isChecked())
        
        for project in projects:
            # Crée l'élément projet
            project_item = QTreeWidgetItem(self.tree)
            project_item.setText(0, project['name'])
            project_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'project', 'id': project['id']})
            
            # Case à cocher pour l'état actif/inactif
            checkbox = QCheckBox()
            checkbox.setChecked(project['is_active'])
            checkbox.stateChanged.connect(lambda state, p=project['id']: self.toggle_project(p, state))
            self.tree.setItemWidget(project_item, 1, checkbox)
            
            # Ajoute les tickets du projet
            for ticket in project['tickets']:
                ticket_item = QTreeWidgetItem(project_item)
                display_text = f"{ticket['ticket_number']} - {ticket['title']}" if ticket['title'] else ticket['ticket_number']
                ticket_item.setText(0, display_text)
                ticket_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'ticket',
                    'project_id': project['id'],
                    'ticket_number': ticket['ticket_number']
                })
                
                # Case à cocher pour l'état actif/inactif du ticket
                ticket_checkbox = QCheckBox()
                ticket_checkbox.setChecked(ticket['is_active'])
                ticket_checkbox.stateChanged.connect(
                    lambda state, p=project['id'], t=ticket['ticket_number']: 
                    self.toggle_ticket(p, t, state)
                )
                self.tree.setItemWidget(ticket_item, 1, ticket_checkbox)
        
        self.tree.expandAll()
        
    def toggle_project(self, project_id, state):
        """Active ou désactive un projet."""
        self.db.toggle_project_active(project_id, state == Qt.CheckState.Checked.value)
        self.load_data()  # Recharge pour refléter les changements
        
    def toggle_ticket(self, project_id, ticket_number, state):
        """Active ou désactive un ticket."""
        self.db.toggle_ticket_active(project_id, ticket_number, state == Qt.CheckState.Checked.value)
        self.load_data()  # Recharge pour refléter les changements
