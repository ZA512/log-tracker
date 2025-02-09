#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget, QCompleter, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent

class ClickableLineEdit(QLineEdit):
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class CustomComboBox(QComboBox):
    def mousePressEvent(self, event):
        """Surcharge de l'événement de clic pour afficher la liste."""
        super().mousePressEvent(event)
        if not self.view().isVisible():
            self.showPopup()

class ParentTicketComboBox(QWidget):
    """Widget personnalisé pour la sélection du ticket parent."""
    
    ticketChanged = pyqtSignal(str)  # Signal émis quand le ticket change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.tickets = []
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ComboBox éditable pour les tickets
        self.combo = CustomComboBox()
        self.combo.setEditable(True)
        
        # Remplace le QLineEdit par notre ClickableLineEdit
        line_edit = ClickableLineEdit()
        line_edit.clicked.connect(self._on_click)
        self.combo.setLineEdit(line_edit)
        
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo.currentTextChanged.connect(self._on_text_changed)
        self.combo.setMinimumWidth(300)  # Un peu plus large pour les chemins
        
        # Configuration de l'autocomplétion
        self.completer = QCompleter([])
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.combo.setCompleter(self.completer)
        
        layout.addWidget(self.combo)
        self.setLayout(layout)
    
    def _on_click(self):
        """Appelé quand l'utilisateur clique sur le champ."""
        self.combo.showPopup()
    
    def _on_text_changed(self, text):
        """Gère le changement de texte dans la combobox."""
        # Extrait juste la clé du ticket si le texte contient un tiret
        ticket_key = text.split(" - ")[0] if " - " in text else text
        self.ticketChanged.emit(ticket_key)
    
    def set_tickets(self, tickets, current_ticket=None):
        """
        Met à jour la liste des tickets disponibles.
        
        Args:
            tickets: Liste des dictionnaires de tickets avec 'ticket_key' et 'path'
            current_ticket: Ticket actuel à sélectionner (optionnel)
        """
        self.tickets = tickets
        
        # Crée les items avec le format "TICKET-123 - path/to/ticket"
        items = [f"{t['ticket_key']} - {t['path']}" for t in tickets]
        
        # Met à jour la combobox et le completer
        self.combo.clear()
        self.combo.addItems(items)
        self.completer.setModel(self.combo.model())
        
        # Sélectionne le ticket approprié si spécifié, sinon laisse vide
        if current_ticket is not None:
            for i in range(self.combo.count()):
                if self.combo.itemText(i).startswith(current_ticket):
                    self.combo.setCurrentIndex(i)
                    break
        else:
            self.combo.setCurrentText("")
    
    def get_current_ticket(self):
        """Retourne la clé du ticket actuellement sélectionné."""
        text = self.combo.currentText()
        return text.split(" - ")[0] if " - " in text else text
    
    def clear(self):
        """Efface le contenu de la combobox."""
        current_items = [self.combo.itemText(i) for i in range(self.combo.count())]
        self.combo.setCurrentText("")
        # On garde les items pour l'autocomplétion
        if current_items:
            self.set_tickets([{'ticket_key': item.split(" - ")[0], 'path': item.split(" - ")[1]} 
                            for item in current_items])
