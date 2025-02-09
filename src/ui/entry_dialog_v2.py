from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QComboBox,
    QTextEdit, QWidget, QGridLayout, QDateEdit, QTimeEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDate, QTime
from PyQt6.QtGui import QIcon
from utils.database import Database
from .theme import Theme, DEFAULT_THEME, get_stylesheet
from .project_combo import ProjectComboBox
from .ticket_combo import TicketComboBox

class TimeButton(QPushButton):
    """Bouton pour sélectionner une durée."""
    def __init__(self, text, minutes, parent=None):
        super().__init__(text, parent)
        self.minutes = minutes
        self.setCheckable(True)
        self.clicked.connect(self.on_clicked)
        
    def on_clicked(self):
        """Gère le clic sur le bouton."""
        # Trouve la fenêtre principale (EntryDialogV2)
        dialog = self
        while dialog and not isinstance(dialog, EntryDialogV2):
            dialog = dialog.parent()
            
        if dialog:
            if self.isChecked():
                dialog.add_duration(self.minutes)
            else:
                dialog.remove_duration(self.minutes)

class EntryDialogV2(QDialog):
    """Nouvelle version de la fenêtre de saisie d'une entrée."""

    def __init__(self, parent=None, db=None, theme: Theme = DEFAULT_THEME):
        super().__init__(parent)
        self.db = db
        self.theme = theme
        self.jira_client = None
        self.setup_jira_client()
        self.total_duration = 0
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setup_ui()
        self.setup_suggestions()
        self.clear_all(init=True)
        self.apply_theme()
        

    def setup_jira_client(self):
        """Configure le client Jira avec les paramètres de la base de données."""
        try:
            base_url = self.db.get_setting('jira_base_url')
            token = self.db.get_setting('jira_token')
            email = self.db.get_setting('jira_email')
            
            if base_url and token and email:
                from utils.jira_client import JiraClient
                self.jira_client = JiraClient(base_url, token, email)
        except Exception as e:
            pass

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Nouvelle entrée")
        self.setFixedWidth(700)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # En-tête - Projet
        self.project_combo = ProjectComboBox()
        self.project_combo.setFixedHeight(25)
        self.project_combo.projectChanged.connect(self.on_project_changed)
        self.project_combo.combo.lineEdit().setPlaceholderText("Choisissez ou créez votre projet")
        main_layout.addWidget(self.project_combo)
        
        # Section FAIT
        done_group = QGroupBox("FAIT")
        done_layout = QVBoxLayout()
        done_layout.setSpacing(5)
        
        # Ligne de ticket
        ticket_layout = QHBoxLayout()
        ticket_layout.setSpacing(5)
        
        # Partie gauche (ticket et titre)
        ticket_title_layout = QHBoxLayout()
        ticket_title_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.ticket_combo = TicketComboBox()
        self.ticket_combo.setFixedHeight(25)
        self.ticket_combo.ticketChanged.connect(self.on_ticket_selected)
        self.ticket_combo.combo.lineEdit().setPlaceholderText("Choisissez ou copiez un ticket")
        
        self.title_input = QLineEdit()
        self.title_input.setFixedHeight(25)
        self.title_input.setPlaceholderText("Le titre sera récupéré automatiquement depuis Jira")
        self.title_input.focusInEvent = self.on_title_focus
        
        add_button = QPushButton("+")
        add_button.setFixedSize(25, 25)
        
        ticket_title_layout.addWidget(self.ticket_combo, stretch=2)
        ticket_title_layout.addWidget(self.title_input, stretch=3)
        ticket_title_layout.addWidget(add_button)
        
        # Partie droite (date et heure)
        datetime_layout = QVBoxLayout()
        datetime_layout.setSpacing(2)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setFixedHeight(25)
        
        self.time_input = QTimeEdit()
        if self.db and self.db.get_setting('use_sequential_time', '0') == '1':
            sequential_time = self.db.get_sequential_time(self.date_input.date().toString("yyyy-MM-dd"))
            self.time_input.setTime(QTime.fromString(sequential_time, "HH:mm"))
        else:
            self.time_input.setTime(QTime.currentTime())
        self.time_input.setDisplayFormat("HH:mm")
        self.time_input.setFixedHeight(25)
        
        datetime_layout.addWidget(self.date_input)
        datetime_layout.addWidget(self.time_input)
        
        # Ajout des layouts à la ligne de ticket
        ticket_layout.addLayout(ticket_title_layout, stretch=1)
        ticket_layout.addLayout(datetime_layout)
        
        done_layout.addLayout(ticket_layout)
        
        # Zone de texte et sélecteur de temps côte à côte
        content_layout = QHBoxLayout()
        
        # Zone de texte pour l'explication
        self.done_text = QTextEdit()
        self.done_text.setPlaceholderText("explication de ce qui a été fait.")
        
        # Sélecteur de temps à droite
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_layout.setSpacing(5)
        time_layout.setContentsMargins(0, 0, 0, 0)
        
        # Heures
        hours_layout = QVBoxLayout()
        hours_label = QLabel("Heure")
        hours_grid = QGridLayout()
        hours_grid.setSpacing(2)
        
        self.hour_buttons = []
        hours = ["1", "2", "3", "4", "5", "6", "7", "8"]
        for i, hour in enumerate(hours):
            btn = TimeButton(hour, int(hour) * 60)
            self.hour_buttons.append(btn)
            hours_grid.addWidget(btn, i//4, i%4)
        
        hours_layout.addWidget(hours_label)
        hours_layout.addLayout(hours_grid)
        
        # Minutes
        minutes_layout = QVBoxLayout()
        minutes_label = QLabel("Minute")
        minutes_grid = QGridLayout()
        minutes_grid.setSpacing(2)
        
        self.minute_buttons = []
        minutes = [("5", 5), ("10", 10), ("15", 15), ("20", 20),
                  ("30", 30), ("40", 40), ("45", 45), ("50", 50)]
        for i, (text, mins) in enumerate(minutes):
            btn = TimeButton(text, mins)
            self.minute_buttons.append(btn)
            minutes_grid.addWidget(btn, i//4, i%4)
        
        minutes_layout.addWidget(minutes_label)
        minutes_layout.addLayout(minutes_grid)
        
        self.duration_label = QPushButton("Durée : 0 minutes")
        self.duration_label.setEnabled(False)
        self.duration_label.setFixedHeight(25)
        
        time_layout.addLayout(hours_layout)
        time_layout.addLayout(minutes_layout)
        time_layout.addWidget(self.duration_label)
        
        # Ajuster la largeur des champs date/heure pour correspondre aux boutons
        button_width = 25 * 4 + 6  # 4 boutons de 25px + 3 espacements de 2px
        self.date_input.setFixedWidth(button_width)
        self.time_input.setFixedWidth(button_width)
        
        # Ajuster la hauteur du QTextEdit pour correspondre au bloc de temps
        time_widget_height = time_widget.sizeHint().height()
        self.done_text.setFixedHeight(time_widget_height)
        
        content_layout.addWidget(self.done_text, stretch=1)
        content_layout.addWidget(time_widget)
        
        done_layout.addLayout(content_layout)
        done_group.setLayout(done_layout)
        main_layout.addWidget(done_group)
        
        # Section À FAIRE
        self.todo_group = QGroupBox("A FAIRE")
        todo_layout = QVBoxLayout()
        todo_layout.setSpacing(5)
        
        # Champ de recherche Epic/Fonctionnalités
        self.epic_input = QLineEdit()
        self.epic_input.setFixedHeight(25)
        self.epic_input.setPlaceholderText("autocompletion tuple EPIC + Fonctionnalités choisit dans l'app")
        todo_layout.addWidget(self.epic_input)
        
        # Titre de la sous-tâche
        self.subtask_title = QLineEdit()
        self.subtask_title.setFixedHeight(25)
        self.subtask_title.setPlaceholderText("Titre de la sous tâche")
        todo_layout.addWidget(self.subtask_title)
        
        # Description du ticket
        self.todo_text = QTextEdit()
        self.todo_text.setPlaceholderText("Description du ticket qui sera créé")
        self.todo_text.setFixedHeight(80)
        todo_layout.addWidget(self.todo_text)
        
        self.todo_group.setLayout(todo_layout)
        main_layout.addWidget(self.todo_group)
        
        # Vérifie si on doit afficher la section "À FAIRE"
        entry_type = self.db.get_setting('entry_screen_type', 'time_only')
        self.todo_group.setVisible(entry_type == 'time_and_todo')
        
        # Boutons OK/Annuler
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.setFixedWidth(80)
        self.ok_button.setFixedHeight(25)
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setFixedWidth(80)
        self.cancel_button.setFixedHeight(25)
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def add_duration(self, minutes):
        """Ajoute des minutes à la durée totale."""
        self.total_duration += minutes
        self.duration_label.setText(f"Durée : {self.total_duration} minutes")

    def remove_duration(self, minutes):
        """Retire des minutes de la durée totale."""
        self.total_duration -= minutes
        self.duration_label.setText(f"Durée : {self.total_duration} minutes")

    def apply_theme(self):
        """Applique le thème actuel à la fenêtre."""
        self.setStyleSheet(get_stylesheet(self.theme))

    def setup_suggestions(self):
        """Initialise les suggestions pour les projets."""
        if self.db:
            try:
                projects = self.db.get_project_suggestions()
                self.project_combo.set_projects(projects)
                self.ticket_combo.set_tickets([])
            except Exception as e:
                pass

    def on_project_changed(self, project_name):
        """Appelé lorsque le projet sélectionné change."""
        if self.db:
            if not project_name:
                self.ticket_combo.set_tickets([])
                return

            # Récupère l'ID du projet
            project = self.db.get_project_by_name(project_name)
            if not project:
                return

            # Récupère les tickets du projet
            tickets = self.db.get_project_tickets(project['id'])
            if tickets:
                # Met à jour la liste des tickets
                self.ticket_combo.set_tickets(tickets)
                # Sélectionne le premier ticket mais sans déclencher la recherche du titre
                first_ticket = tickets[0]['ticket_number']
                self.ticket_combo.setText(first_ticket)
            else:
                self.ticket_combo.set_tickets([])

    def on_ticket_selected(self, ticket_number):
        """Appelé lorsqu'un ticket est sélectionné."""
        if ticket_number and self.jira_client:
            self.fetch_ticket_title_from_jira(ticket_number)

    def fetch_ticket_title_from_jira(self, ticket_number):
        """Récupère le titre du ticket depuis Jira."""
        if self.jira_client:
            try:
                issue = self.jira_client.get_issue_details(ticket_number)
                if issue:
                    self.title_input.setText(issue['summary'])
            except Exception as e:
                pass

    def on_title_focus(self, event):
        """Appelé lorsque le champ titre reçoit le focus."""
        ticket_number = self.ticket_combo.combo.currentText()
        if ticket_number and self.jira_client:
            self.fetch_ticket_title_from_jira(ticket_number)

    def clear_all(self, init=False):
        """Efface tous les champs."""
        if not init:
            self.project_combo.combo.setCurrentText("") 
            self.ticket_combo.combo.setCurrentText("")
            self.title_input.clear()
            self.done_text.clear()
            self.todo_text.clear()
            self.epic_input.clear()
            self.subtask_title.clear()
            
            # Réinitialise les boutons de temps
            for btn in self.hour_buttons + self.minute_buttons:
                btn.setChecked(False)
            self.total_duration = 0
            self.duration_label.setText("Durée : 0 minutes")

    def showEvent(self, event):
        """Appelé lorsque la fenêtre est affichée."""
        self.clear_all()
        super().showEvent(event)

    def reject(self):
        """Appelé lorsque l'utilisateur clique sur Annuler."""
        self.clear_all()
        super().reject()

    def closeEvent(self, event):
        """Appelé lorsque la fenêtre est fermée."""
        self.clear_all()
        super().closeEvent(event)
