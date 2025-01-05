from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal

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
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo.currentTextChanged.connect(self._on_text_changed)
        self.combo.setMinimumWidth(200)  # Largeur minimale
        layout.addWidget(self.combo)
        
        self.setLayout(layout)
    
    def _on_text_changed(self, text):
        """Gère le changement de texte dans la combobox."""
        self.projectChanged.emit(text)
    
    def set_projects(self, projects, current_project=None):
        """
        Met à jour la liste des projets disponibles.
        
        Args:
            projects: Liste des projets disponibles
            current_project: Projet actuel à sélectionner (optionnel)
        """
        self.projects = projects
        
        # Sauvegarde le texte actuel
        current_text = self.combo.currentText()
        
        # Met à jour la combobox
        self.combo.clear()
        self.combo.addItems(projects)
        
        # Sélectionne le projet approprié
        if current_project is not None:
            index = self.combo.findText(current_project)
            if index >= 0:
                self.combo.setCurrentIndex(index)
        elif current_text in projects:
            index = self.combo.findText(current_text)
            if index >= 0:
                self.combo.setCurrentIndex(index)
    
    def clear(self):
        """Efface le contenu de la combobox."""
        self.combo.setCurrentText("")
    
    def text(self):
        """Retourne le texte actuel."""
        return self.combo.currentText()
    
    def setText(self, text):
        """Définit le texte de la combobox."""
        self.combo.setCurrentText(text)
