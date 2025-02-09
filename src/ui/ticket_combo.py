from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
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

class TicketComboBox(QWidget):
    """Widget personnalisé pour la saisie et la sélection de tickets."""
    
    ticketChanged = pyqtSignal(str)  # Signal émis quand le ticket change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.tickets = []
        self.ticket_data = {}  # Stocke les données complètes des tickets
        self.is_new_ticket = False
    
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
        self.combo.currentIndexChanged.connect(self._on_index_changed)
        self.combo.setMinimumWidth(200)  # Largeur minimale
        
        # Permettre à l'utilisateur de taper directement un numéro de ticket
        self.combo.lineEdit().textChanged.connect(self._on_text_changed)
        
        layout.addWidget(self.combo)
        
        # Label pour le nombre de tickets
        self.count_label = QLabel("")
        layout.addWidget(self.count_label)
        
        self.setLayout(layout)
        
        # Style pour le label de compteur
        self.count_label.setStyleSheet("color: gray;")
    
    def _on_click(self):
        """Appelé quand l'utilisateur clique sur le champ."""
        self.combo.showPopup()
    
    def _on_index_changed(self, index):
        """Appelé quand l'index de la combobox change."""
        if index == 0:  # Option "Nouveau ticket"
            self.is_new_ticket = True
            QTimer.singleShot(0, lambda: self.combo.setEditText(""))
            self.ticketChanged.emit("")
        elif index > 0:  # Un ticket existant
            self.is_new_ticket = False
            ticket_number = self.combo.itemData(index)
            # Utilise un QTimer pour s'assurer que le texte est mis à jour après le changement d'index
            QTimer.singleShot(0, lambda: self.combo.setEditText(ticket_number))
            self.ticketChanged.emit(ticket_number)
    
    def _on_text_changed(self, text):
        """Gère la saisie manuelle de texte."""
        # Si le texte est différent des tickets existants, c'est un nouveau ticket
        if text and text not in self.tickets:
            self.is_new_ticket = True
        self.ticketChanged.emit(text)
    
    def _show_popup(self, event):
        """Affiche la liste déroulante au clic ou au focus."""
        self.combo.showPopup()
        # Appelle l'événement original
        if isinstance(event, QEvent.Type.FocusIn):
            super(type(self.combo.lineEdit()), self.combo.lineEdit()).focusInEvent(event)
        else:
            super(type(self.combo.lineEdit()), self.combo.lineEdit()).mouseReleaseEvent(event)
    
    def set_tickets(self, tickets, current_ticket=None):
        """
        Met à jour la liste des tickets disponibles.
        
        Args:
            tickets: Liste des tickets avec leurs titres
            current_ticket: Ticket actuel à sélectionner (optionnel)
        """
        self.tickets = [ticket['ticket_number'] for ticket in tickets]
        self.ticket_data = {ticket['ticket_number']: ticket for ticket in tickets}
        
        # Met à jour la combobox avec les tickets et leurs titres
        self.combo.clear()
        
        # Ajoute l'option "Nouveau ticket"
        self.combo.addItem("Nouveau ticket", None)
        
        # Ajoute les tickets existants
        for ticket in tickets:
            display_text = f"{ticket['ticket_number']} - {ticket['title']}" if ticket['title'] else ticket['ticket_number']
            self.combo.addItem(display_text, ticket['ticket_number'])
        
        # Sélectionne le ticket approprié
        if current_ticket is not None:
            index = self.combo.findData(current_ticket)
            if index >= 0:
                self.combo.setCurrentIndex(index)
        elif self.tickets:
            self.combo.setCurrentIndex(1)  # Sélectionne le premier ticket existant
        
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
        self.combo.clear()
        self.combo.addItem("Nouveau ticket", None)
        self.ticket_data = {}
        self.is_new_ticket = True
    
    def text(self):
        """Retourne le texte actuel (numéro de ticket uniquement)."""
        return self.combo.currentText()
    
    def setText(self, text):
        """Définit le texte de la combobox."""
        if not text:
            self.combo.setCurrentIndex(0)  # Sélectionne "Nouveau ticket"
            self.is_new_ticket = True
        else:
            index = self.combo.findData(text)
            if index >= 0:
                self.combo.setCurrentIndex(index)
                self.is_new_ticket = False
            else:
                self.combo.setEditText(text)
                self.is_new_ticket = True
