from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QMessageBox, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor
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
        self.setModal(True)
        self.resize(1000, 600)
        
        layout = QVBoxLayout()
        
        # En-tête
        header_label = QLabel("Entrées à synchroniser avec Jira")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header_label)
        
        # Liste des entrées
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Date", "Projet", "Ticket", "Description", "Durée"])
        self.tree.setColumnWidth(0, 150)  # Date
        self.tree.setColumnWidth(1, 150)  # Projet
        self.tree.setColumnWidth(2, 100)  # Ticket
        self.tree.setColumnWidth(3, 450)  # Description
        self.tree.setColumnWidth(4, 100)  # Durée
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)
        
        # Barre de progression
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Légende
        legend_label = QLabel("Les entrées sans ticket sont marquées en orange")
        legend_label.setStyleSheet("color: #FF8C00;")
        layout.addWidget(legend_label)
        
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
            item = QTreeWidgetItem()
            
            # Date et heure
            timestamp = QDateTime.fromString(entry['timestamp'], Qt.DateFormat.ISODate)
            item.setText(0, timestamp.toString("dd/MM/yyyy HH:mm"))
            
            # Projet et ticket
            item.setText(1, entry.get('project_name', ''))
            ticket = entry.get('ticket_number', '')
            item.setText(2, ticket)
            
            # Description (avec le titre du ticket si disponible)
            description = entry.get('description', '')
            if entry.get('ticket_title'):
                description = f"{entry['ticket_title']}\n{description}"
            item.setText(3, description)
            
            # Durée
            duration = entry.get('duration', 0)
            item.setText(4, f"{duration}h")
            
            # Colore en orange les entrées sans ticket
            if not ticket:
                for col in range(5):
                    item.setBackground(col, QColor(255, 200, 100))
            
            # Stocke l'ID pour la synchronisation
            item.setData(0, Qt.ItemDataRole.UserRole, entry['id'])
            
            self.tree.addTopLevelItem(item)
    
    def sync_with_jira(self):
        """Synchronise les entrées avec Jira."""
        # Vérifie la configuration Jira
        jira_url = self.db.get_setting('jira_url')
        jira_token = self.db.get_setting('jira_token')
        
        if not jira_url or not jira_token:
            QMessageBox.warning(
                self,
                "Configuration manquante",
                "Veuillez configurer l'URL et le token Jira dans les paramètres."
            )
            return
        
        # Initialise le client Jira
        jira = JiraClient(jira_url, jira_token)
        
        # Prépare la synchronisation
        entries_count = self.tree.topLevelItemCount()
        self.progress.setMaximum(entries_count)
        self.progress.setValue(0)
        self.progress.show()
        self.sync_button.setEnabled(False)
        
        # Synchronise chaque entrée
        synced_ids = []
        errors = []
        
        for i in range(entries_count):
            item = self.tree.topLevelItem(i)
            entry_id = item.data(0, Qt.ItemDataRole.UserRole)
            ticket = item.text(2)
            description = item.text(3)
            duration = float(item.text(4).rstrip('h'))
            
            # Si pas de ticket, marque comme synchronisé et continue
            if not ticket:
                synced_ids.append(entry_id)
                self.progress.setValue(i + 1)
                continue
            
            # Tente d'ajouter le worklog
            if jira.add_worklog(ticket, int(duration * 60), description):
                synced_ids.append(entry_id)
            else:
                errors.append(f"Erreur lors de la synchronisation du ticket {ticket}")
            
            self.progress.setValue(i + 1)
        
        # Marque les entrées comme synchronisées
        if synced_ids:
            self.db.mark_entries_as_synced(synced_ids)
        
        # Masque la barre de progression
        self.progress.hide()
        self.sync_button.setEnabled(True)
        
        # Affiche le résultat
        if errors:
            QMessageBox.warning(
                self,
                "Erreurs de synchronisation",
                "Des erreurs sont survenues lors de la synchronisation :\n\n" + "\n".join(errors)
            )
        else:
            QMessageBox.information(
                self,
                "Synchronisation terminée",
                f"{len(synced_ids)} entrée(s) synchronisée(s) avec succès."
            )
        
        # Recharge les entrées
        self.load_entries()
