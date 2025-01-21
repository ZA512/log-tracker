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
        self.tree.setHeaderLabels(["Date", "Projet", "Ticket", "Fait", "Durée"])
        self.tree.setColumnWidth(0, 150)  # Date
        self.tree.setColumnWidth(1, 150)  # Projet
        self.tree.setColumnWidth(2, 100)  # Ticket
        self.tree.setColumnWidth(3, 450)  # Description
        self.tree.setColumnWidth(4, 100)  # Durée
        
        # Configuration des couleurs et de l'alignement
        self.tree.setStyleSheet("""
            QTreeWidget {
                alternate-background-color: #2d4f6c;
            }
            QTreeWidget::item {
                padding-top: 0;
                padding-bottom: 0;
                alignment: top;
            }
        """)
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
            timestamp = QDateTime.fromString(f"{entry['date']} {entry['time']}", "yyyy-MM-dd HH:mm")
            item.setText(0, timestamp.toString("dd/MM/yyyy HH:mm"))
            item.setTextAlignment(0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

            # Projet et ticket
            item.setText(1, entry.get('project_name', ''))
            item.setTextAlignment(1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            
            ticket = entry.get('ticket_number', '')
            item.setText(2, ticket)
            item.setTextAlignment(2, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

            # Description (avec le titre du ticket si disponible)
            description = entry.get('description', '')
            if entry.get('ticket_title'):
                description = f"{entry['ticket_title']}\n{description}"
            item.setText(3, description)
            item.setTextAlignment(3, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

            # Durée
            duration = entry.get('duration', 0)
            item.setText(4, self.minutes_to_hhmm(duration))
            item.setTextAlignment(4, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

            # Application des couleurs
            if not ticket:
                # Entrées sans ticket en orange (sauf durée)
                orange_color = QColor("#FF8C00")
                for col in range(5):
                    if col != 4:  # On ne change pas la couleur de la durée
                        item.setForeground(col, orange_color)
            else:
                # Ticket en bleu
                item.setForeground(2, QColor("#64b5f6"))
            
            # Durée toujours en vert
            item.setForeground(4, QColor("#81c784"))

            # Stocke l'ID pour la synchronisation
            item.setData(0, Qt.ItemDataRole.UserRole, entry['id'])

            self.tree.addTopLevelItem(item)

    def minutes_to_hhmm(self, minutes):
        """Convertit une durée en minutes en format hh:mm."""
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours:02d}h{remaining_minutes:02d}"

    def sync_with_jira(self):
        """Synchronise les entrées avec Jira."""
        # Vérifie la configuration Jira
        base_url = self.db.get_setting('jira_base_url')
        token = self.db.get_setting('jira_token')
        email = self.db.get_setting('jira_email')
        
        if not base_url or not token or not email:
            QMessageBox.warning(
                self,
                "Configuration manquante",
                "Veuillez configurer l'URL, l'email et le token Jira dans les paramètres."
            )
            return
        
        # Initialise le client Jira
        jira = JiraClient(base_url, token, email)
        
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
            duration = float(item.text(4).rstrip('h').split('h')[0]) * 60 + float(item.text(4).rstrip('h').split('h')[1].rstrip('m'))  # Convertit en minutes
            
            # Récupère la date et l'heure de l'entrée depuis la base de données
            entry = self.db.get_entry_by_id(entry_id)
            entry_datetime = QDateTime.fromString(f"{entry['date']} {entry['time']}", "yyyy-MM-dd HH:mm").toPyDateTime()
            
            # Si pas de ticket, marque comme synchronisé et continue
            if not ticket:
                synced_ids.append(entry_id)
                self.progress.setValue(i + 1)
                continue
            
            # Tente d'ajouter le worklog
            if jira.add_worklog(ticket, int(duration), description, entry_datetime):
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
