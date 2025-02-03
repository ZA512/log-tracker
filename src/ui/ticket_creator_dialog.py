from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QTextEdit, QDialogButtonBox,
    QComboBox, QLabel
)
from PyQt6.QtCore import Qt
from typing import Optional, Dict

class TicketCreatorDialog(QDialog):
    """Fenêtre de création d'un nouveau ticket Jira."""

    def __init__(self, parent=None, epic_key: Optional[str] = None, feature_key: Optional[str] = None):
        super().__init__(parent)
        self.epic_key = epic_key
        self.feature_key = feature_key
        self.setup_ui()
        if epic_key and feature_key:
            self.epic_combo.setCurrentText(epic_key)
            self.feature_combo.setCurrentText(feature_key)

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Créer un nouveau ticket")
        layout = QVBoxLayout()

        form = QFormLayout()

        # Type de ticket
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Tâche", "Sous-tâche", "Bug"])
        form.addRow("Type:", self.type_combo)

        # Epic
        self.epic_combo = QComboBox()
        self.epic_combo.setEditable(True)
        form.addRow("Epic:", self.epic_combo)

        # Fonctionnalité
        self.feature_combo = QComboBox()
        self.feature_combo.setEditable(True)
        form.addRow("Fonctionnalité:", self.feature_combo)

        # Résumé
        self.summary_input = QLineEdit()
        form.addRow("Résumé:", self.summary_input)

        # Description
        self.description_input = QTextEdit()
        form.addRow("Description:", self.description_input)

        layout.addLayout(form)

        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def set_epics(self, epics: Dict[str, str]):
        """Définit la liste des epics disponibles.
        
        Args:
            epics: Dictionnaire {epic_key: epic_name}
        """
        self.epic_combo.clear()
        for key, name in epics.items():
            self.epic_combo.addItem(name, key)

    def set_features(self, features: Dict[str, str]):
        """Définit la liste des fonctionnalités disponibles.
        
        Args:
            features: Dictionnaire {feature_key: feature_name}
        """
        self.feature_combo.clear()
        for key, name in features.items():
            self.feature_combo.addItem(name, key)

    def get_ticket_data(self) -> Dict:
        """Retourne les données du ticket à créer."""
        return {
            "type": self.type_combo.currentText(),
            "epic_key": self.epic_combo.currentData(),
            "feature_key": self.feature_combo.currentData(),
            "summary": self.summary_input.text(),
            "description": self.description_input.toPlainText()
        }
