from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime
from utils.database import Database
from utils.jira_client import JiraClient


class SyncDialog(QDialog):
    """Fenêtre de synchronisation avec Jira."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.setup_ui()
        self.load_entries()
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Synchronisation Jira")
        self.resize(800, 500)
        
        layout = QVBoxLayout()
        
        # Liste des entrées
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Date", "Projet", "Ticket", "Description", "Durée"])
        self.tree.setColumnWidth(0, 150)  # Date
        self.tree.setColumnWidth(1, 100)  # Projet
        self.tree.setColumnWidth(2, 100)  # Ticket
        self.tree.setColumnWidth(3, 350)  # Description
        self.tree.setWordWrap(True)
        layout.addWidget(self.tree)
        
        # Bouton de synchronisation
        self.sync_button = QPushButton("Synchroniser avec Jira")
        self.sync_button.clicked.connect(self.sync_with_jira)
        layout.addWidget(self.sync_button)
        
        self.setLayout(layout)
    
    def load_entries(self):
        """Charge les entrées non synchronisées."""
        self.tree.clear()
        entries = self.db.get_unsynchronized_entries()
        
        for entry in entries:
            item = QTreeWidgetItem(self.tree)
            timestamp = datetime.fromisoformat(entry['timestamp'])
            
            item.setText(0, timestamp.strftime('%d/%m/%Y %H:%M'))
            item.setText(1, entry.get('project_name', ''))
            item.setText(2, entry.get('ticket_number', ''))
            item.setText(3, entry.get('description', ''))
            item.setText(4, f"{entry.get('duration', 0)}h")
            
            # Colore en orange les entrées sans ticket
            if not entry.get('ticket_number'):
                for col in range(5):
                    item.setBackground(col, QColor(255, 200, 100))
            
            # Stocke l'ID pour la synchronisation
            item.setData(0, Qt.ItemDataRole.UserRole, entry['id'])
    
    def sync_with_jira(self):
        """Synchronise les entrées avec Jira."""
        # Récupère les paramètres Jira
        jira_url = self.db.get_setting('jira_url')
        jira_token = self.db.get_setting('jira_token')
        
        if not jira_url or not jira_token:
            QMessageBox.warning(self, "Erreur", "Veuillez configurer l'URL et le token Jira dans les paramètres.")
            return
        
        # Initialise le client Jira
        jira = JiraClient(jira_url, jira_token)
        
        # Récupère toutes les entrées
        synced_ids = []
        errors = []
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            entry_id = item.data(0, Qt.ItemDataRole.UserRole)
            ticket = item.text(2)
            description = item.text(3)
            duration = float(item.text(4).rstrip('h'))
            
            # Si pas de ticket, marque comme synchronisé et continue
            if not ticket:
                synced_ids.append(entry_id)
                continue
            
            # Tente d'ajouter le worklog
            if jira.add_worklog(ticket, int(duration * 60), description):
                synced_ids.append(entry_id)
            else:
                errors.append(f"Erreur lors de la synchronisation du ticket {ticket}")
        
        # Marque les entrées comme synchronisées
        if synced_ids:
            self.db.mark_entries_as_synced(synced_ids)
        
        # Affiche le résultat
        if errors:
            QMessageBox.warning(self, "Erreurs", "\n".join(errors))
        else:
            QMessageBox.information(self, "Succès", "Synchronisation terminée avec succès")
        
        # Recharge les entrées
        self.load_entries()
