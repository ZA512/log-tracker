#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

class TicketSearchDialog(QDialog):
    """Fenêtre de recherche de tickets dans jira_subtasks."""
    
    # Signal émis quand un ticket est sélectionné
    ticketSelected = pyqtSignal(str, str)  # ticket_number, title
    
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.all_items = []  # Initialisation de la liste
        self.setup_ui()
        self.load_tickets()
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Recherche de tickets")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Zone de recherche
        search_layout = QHBoxLayout()
        search_label = QLabel("Rechercher:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tapez pour filtrer les tickets...")
        self.search_input.textChanged.connect(self._filter_tickets)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Liste des tickets
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Numéro", "Titre", "Chemin"])
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # Ajuste la taille des colonnes
        self.tree.setColumnWidth(0, 150)  # Numéro
        self.tree.setColumnWidth(1, 400)  # Titre
        layout.addWidget(self.tree)
        
        self.setLayout(layout)
    
    def load_tickets(self):
        """Charge tous les tickets depuis la table jira_subtasks."""
        try:
            tickets = self.db.get_all_subtasks()
            
            for ticket in tickets:
                item = QTreeWidgetItem([
                    ticket['ticket_number'],
                    ticket['title'] or '',
                    ticket['path'] or ''
                ])
                self.all_items.append(item)
                self.tree.addTopLevelItem(item)
                
        except Exception as e:
            print(f"Erreur lors du chargement des tickets : {str(e)}")
    
    def _filter_tickets(self, text):
        """Filtre les tickets selon le texte saisi."""
        # Cache d'abord tous les items
        for item in self.all_items:
            item.setHidden(True)
        
        # Si le texte est vide, montre tout
        if not text.strip():
            for item in self.all_items:
                item.setHidden(False)
            return
        
        # Sinon, filtre selon le texte
        search_terms = text.lower().split()
        for item in self.all_items:
            # Combine tous les champs pour la recherche
            item_text = ' '.join([
                item.text(0).lower(),  # Numéro
                item.text(1).lower(),  # Titre
                item.text(2).lower()   # Chemin
            ])
            
            # Vérifie si tous les termes de recherche sont présents
            matches = all(term in item_text for term in search_terms)
            item.setHidden(not matches)
    
    def _on_item_double_clicked(self, item, column):
        """Appelé quand un ticket est double-cliqué."""
        ticket_number = item.text(0)
        title = item.text(1)
        self.ticketSelected.emit(ticket_number, title)
        self.accept()  # Ferme la fenêtre
