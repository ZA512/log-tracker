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

class ProjectComboBox(QWidget):
    """Widget personnalisé pour la sélection de projets."""
    
    projectChanged = pyqtSignal(str)  # Signal émis quand le projet change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.projects = []
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ComboBox éditable pour les projets
        self.combo = CustomComboBox()
        self.combo.setEditable(True)
        
        # Remplace le QLineEdit par notre ClickableLineEdit
        line_edit = ClickableLineEdit()
        line_edit.clicked.connect(self._on_click)
        self.combo.setLineEdit(line_edit)
        
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo.currentTextChanged.connect(self._on_text_changed)
        self.combo.setMinimumWidth(200)  # Largeur minimale
        
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
        self.projectChanged.emit(text)
    
    def _show_popup(self, event):
        """Affiche la liste déroulante au clic ou au focus."""
        self.combo.showPopup()
        # Appelle l'événement original
        if isinstance(event, QEvent.Type.FocusIn):
            super(type(self.combo.lineEdit()), self.combo.lineEdit()).focusInEvent(event)
        else:
            super(type(self.combo.lineEdit()), self.combo.lineEdit()).mouseReleaseEvent(event)
    
    def set_projects(self, projects, current_project=None):
        """
        Met à jour la liste des projets disponibles.
        
        Args:
            projects: Liste des projets disponibles
            current_project: Projet actuel à sélectionner (optionnel)
        """
        self.projects = projects
        
        # Met à jour la combobox et le completer
        self.combo.clear()
        self.combo.addItems(projects)
        self.completer.setModel(self.combo.model())
        
        # Sélectionne le projet approprié si spécifié, sinon laisse vide
        if current_project is not None:
            index = self.combo.findText(current_project)
            if index >= 0:
                self.combo.setCurrentIndex(index)
        else:
            self.combo.setCurrentText("")
    
    def clear(self):
        """Efface le contenu de la combobox."""
        current_items = [self.combo.itemText(i) for i in range(self.combo.count())]
        self.combo.setCurrentText("")
        # On garde les items pour l'autocomplétion
        if current_items:
            self.set_projects(current_items)
    
    def text(self):
        """Retourne le texte actuel."""
        return self.combo.currentText()
    
    def setText(self, text):
        """Définit le texte de la combobox."""
        self.combo.setCurrentText(text)
    
    def setFocus(self):
        """Met le focus sur la combobox."""
        self.combo.setFocus()
        # Sélectionne tout le texte pour faciliter la saisie
        self.combo.lineEdit().selectAll()
