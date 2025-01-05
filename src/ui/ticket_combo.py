from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal

class TicketComboBox(QWidget):
    """Widget personnalisé pour la saisie et la sélection de tickets."""
    
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
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo.currentTextChanged.connect(self._on_text_changed)
        self.combo.setMinimumWidth(200)  # Largeur minimale
        layout.addWidget(self.combo)
        
        # Label pour le nombre de tickets
        self.count_label = QLabel("")
        layout.addWidget(self.count_label)
        
        self.setLayout(layout)
        
        # Style pour le label de compteur
        self.count_label.setStyleSheet("color: gray;")
    
    def _on_text_changed(self, text):
        """Gère le changement de texte dans la combobox."""
        self.ticketChanged.emit(text)
    
    def set_tickets(self, tickets, current_ticket=None):
        """
        Met à jour la liste des tickets disponibles.
        
        Args:
            tickets: Liste des tickets disponibles
            current_ticket: Ticket actuel à sélectionner (optionnel)
        """
        self.tickets = tickets
        
        # Sauvegarde le texte actuel
        current_text = self.combo.currentText()
        
        # Met à jour la combobox
        self.combo.clear()
        self.combo.addItems(tickets)
        
        # Sélectionne le ticket approprié
        if current_ticket is not None:
            index = self.combo.findText(current_ticket)
            if index >= 0:
                self.combo.setCurrentIndex(index)
        elif current_text in tickets:
            index = self.combo.findText(current_text)
            if index >= 0:
                self.combo.setCurrentIndex(index)
        elif tickets:
            self.combo.setCurrentIndex(0)
        
        # Met à jour le compteur
        self._update_count_label()
    
    def _update_count_label(self):
        """Met à jour le label du nombre de tickets."""
        count = len(self.tickets)
        if count > 0:
            self.count_label.setText(f"({count})")
        else:
            self.count_label.setText("")
    
    def clear(self):
        """Efface le contenu de la combobox."""
        self.combo.setCurrentText("")
    
    def text(self):
        """Retourne le texte actuel."""
        return self.combo.currentText()
    
    def setText(self, text):
        """Définit le texte de la combobox."""
        self.combo.setCurrentText(text)
