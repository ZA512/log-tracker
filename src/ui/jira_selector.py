from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QPushButton, QLineEdit, QCompleter
)
from PyQt6.QtCore import pyqtSignal, Qt
from typing import Optional, List, Tuple

class JiraSelector(QWidget):
    """Widget pour la sélection d'Epic et de Fonctionnalité Jira."""
    
    selection_changed = pyqtSignal(str, str)  # epic_key, feature_key
    search_requested = pyqtSignal()
    create_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recent_pairs = []  # Liste des tuples (epic, feature) récemment utilisés
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Combobox pour les paires récentes
        self.recent_combo = QComboBox()
        self.recent_combo.setPlaceholderText("Sélectionner Epic/Fonctionnalité récent")
        self.recent_combo.currentIndexChanged.connect(self._on_recent_selected)
        layout.addWidget(self.recent_combo, stretch=2)

        # Champ de recherche
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Rechercher Epic/Fonctionnalité")
        self.search_field.returnPressed.connect(self.search_requested.emit)
        layout.addWidget(self.search_field, stretch=2)

        # Bouton de création
        self.create_button = QPushButton("Nouveau")
        self.create_button.clicked.connect(self.create_requested.emit)
        layout.addWidget(self.create_button)

        self.setLayout(layout)

    def set_recent_pairs(self, pairs: List[Tuple[str, str, str, str]]):
        """Met à jour la liste des paires récentes.
        
        Args:
            pairs: Liste de tuples (epic_key, epic_name, feature_key, feature_name)
        """
        self.recent_pairs = pairs
        self.recent_combo.clear()
        for epic_key, epic_name, feature_key, feature_name in pairs:
            self.recent_combo.addItem(
                f"{epic_name} / {feature_name}",
                (epic_key, feature_key)
            )

    def get_selected_pair(self) -> Optional[Tuple[str, str]]:
        """Retourne la paire (epic_key, feature_key) sélectionnée."""
        idx = self.recent_combo.currentIndex()
        if idx >= 0:
            return self.recent_combo.itemData(idx)
        return None

    def get_search_text(self) -> str:
        """Retourne le texte de recherche."""
        return self.search_field.text()

    def _on_recent_selected(self, index: int):
        """Appelé quand une paire récente est sélectionnée."""
        if index >= 0:
            epic_key, feature_key = self.recent_combo.itemData(index)
            self.selection_changed.emit(epic_key, feature_key)
