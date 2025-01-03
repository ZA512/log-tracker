from PyQt6.QtWidgets import QLineEdit, QCompleter
from PyQt6.QtCore import Qt


class AutocompleteLineEdit(QLineEdit):
    """Champ de saisie avec auto-complétion."""
    
    def __init__(self, completions=None, parent=None):
        super().__init__(parent)
        self.completions = completions or []
        self.setup_completer()
    
    def setup_completer(self):
        """Configure l'auto-complétion."""
        completer = QCompleter(self.completions)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(completer)
    
    def update_completions(self, completions):
        """Met à jour la liste des suggestions."""
        self.completions = completions
        self.setup_completer()
