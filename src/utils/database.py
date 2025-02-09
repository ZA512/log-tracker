import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import os
import json
from PyQt6.QtCore import QDate

class Database:
    """Gestionnaire de la base de données SQLite."""
    
    def __init__(self):
        """Initialise la connexion à la base de données."""
        self.db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, 'logtracker.db')
        self.conn = None
        self.cursor = None
        self.create_tables()
        self.migrate_database()
    
    def connect(self):
        """Établit une connexion à la base de données."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
    
    def disconnect(self):
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def create_tables(self):
        """Crée les tables de la base de données."""
        try:
            self.connect()
            
            # Table des paramètres
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Table des projets
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    ticket_prefix TEXT,
                    planner_id TEXT,  -- ID du plan Planner associé
                    planner_name TEXT -- Nom du plan Planner
                )
            """)
            
            # Table des tickets
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    ticket_number TEXT NOT NULL,
                    title TEXT,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (project_id) REFERENCES projects (id),
                    UNIQUE(project_id, ticket_number)
                )
            """)
            
            # Table des entrées
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    project_id INTEGER,
                    ticket_id INTEGER,
                    ticket_number TEXT,
                    ticket_title TEXT,
                    description TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    is_synced INTEGER DEFAULT 0,
                    planner_task_id TEXT,  -- ID de la tâche Planner si synchronisée
                    FOREIGN KEY (project_id) REFERENCES projects (id),
                    FOREIGN KEY (ticket_id) REFERENCES tickets (id)
                )
            """)
            
            # Suppression des anciennes tables
            self.cursor.execute("DROP TABLE IF EXISTS jira_hierarchy")
            self.cursor.execute("DROP TABLE IF EXISTS epic_feature_pairs")
            self.cursor.execute("DROP TABLE IF EXISTS features")
            self.cursor.execute("DROP TABLE IF EXISTS epics")
            
            # Création des nouvelles tables simplifiées
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS jira_paths (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,  -- Format: "projet/epic/fonctionnalité"
                    ticket_key TEXT NOT NULL,  -- Numéro du ticket Jira
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS jira_subtasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,  -- Format: "projet/epic/fonctionnalité"
                    title TEXT NOT NULL,  -- Titre du ticket
                    ticket_key TEXT NOT NULL,  -- Numéro du ticket Jira
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Création des index pour optimiser les recherches
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_jira_paths_path ON jira_paths(path)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_jira_subtasks_path ON jira_subtasks(path)")
            
            # Ajout des paramètres par défaut
            self.cursor.execute("""
                INSERT OR IGNORE INTO settings (key, value) VALUES 
                    ('jira_base_url', NULL),
                    ('jira_token', NULL),
                    ('jira_email', NULL),
                    ('daily_hours', '8'),
                    ('token_expiry', NULL),
                    ('start_time', '08:00'),
                    ('end_time', '18:00'),
                    ('use_sequential_time', '0'),
                    ('ticket_selection_jql', NULL),
                    ('project_selection_jql', NULL)
            """)
            
            self.conn.commit()
            
        finally:
            self.disconnect()
    
    def migrate_database(self):
        """Effectue les migrations nécessaires de la base de données."""
        try:
            self.connect()
            
            # Vérifie si la colonne planner_id existe dans la table projects
            self.cursor.execute("PRAGMA table_info(projects)")
            columns = [col[1] for col in self.cursor.fetchall()]
            
            if 'planner_id' not in columns:
                self.cursor.execute("ALTER TABLE projects ADD COLUMN planner_id TEXT")
                self.cursor.execute("ALTER TABLE projects ADD COLUMN planner_name TEXT")
                
            # Vérifie si la colonne planner_task_id existe dans la table entries
            self.cursor.execute("PRAGMA table_info(entries)")
            columns = [col[1] for col in self.cursor.fetchall()]
            
            if 'planner_task_id' not in columns:
                self.cursor.execute("ALTER TABLE entries ADD COLUMN planner_task_id TEXT")
                
            self.conn.commit()
        finally:
            self.disconnect()
    
    def add_project(self, name):
        """
        Ajoute un projet.
        
        Args:
            name: Nom du projet
            
        Returns:
            ID du projet
        """
        self.connect()
        try:
            self.cursor.execute("INSERT INTO projects (name) VALUES (?)", (name,))
            self.conn.commit()
            return self.cursor.lastrowid
        finally:
            self.disconnect()
    
    def add_ticket(self, project_id, ticket_number, title=None):
        """
        Ajoute un ticket.
        
        Args:
            project_id: ID du projet
            ticket_number: Numéro du ticket
            title: Titre du ticket (optionnel)
            
        Returns:
            ID du ticket
        """
        self.connect()
        try:
            self.cursor.execute("""
                INSERT INTO tickets (project_id, ticket_number, title)
                VALUES (?, ?, ?)
            """, (project_id, ticket_number, title))
            self.conn.commit()
            return self.cursor.lastrowid
        finally:
            self.disconnect()
    
    def update_ticket_title(self, ticket_id, title):
        """
        Met à jour le titre d'un ticket.
        
        Args:
            ticket_id: ID du ticket
            title: Nouveau titre du ticket
        """
        self.connect()
        try:
            self.cursor.execute("UPDATE tickets SET title = ? WHERE id = ?", (title, ticket_id))
            self.conn.commit()
        finally:
            self.disconnect()
    
    def get_ticket_info(self, project_id, ticket_number):
        """
        Récupère les informations d'un ticket.
        
        Args:
            project_id: ID du projet
            ticket_number: Numéro du ticket
            
        Returns:
            Tuple contenant l'ID, le numéro et le titre du ticket
        """
        self.connect()
        try:
            self.cursor.execute("""
                SELECT id, ticket_number, title
                FROM tickets
                WHERE project_id = ? AND ticket_number = ?
            """, (project_id, ticket_number))
            return self.cursor.fetchone()
        finally:
            self.disconnect()
    
    def get_tickets_for_project(self, project_id):
        """
        Récupère tous les tickets d'un projet avec leurs titres.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste de tuples contenant l'ID, le numéro et le titre de chaque ticket
        """
        self.connect()
        try:
            self.cursor.execute("""
                SELECT id, ticket_number, title
                FROM tickets
                WHERE project_id = ?
                ORDER BY ticket_number DESC
            """, (project_id,))
            return self.cursor.fetchall()
        finally:
            self.disconnect()
    
    def add_entry(self, description, project_id=None, ticket_id=None, duration=60, ticket_title=None, date=None, time=None):
        """Ajoute une nouvelle entrée."""
        self.connect()
        try:
            self.cursor.execute("""
                INSERT INTO entries (
                    date, time, project_id, ticket_id, ticket_title,
                    description, duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                date or datetime.now().strftime("%Y-%m-%d"),
                time or datetime.now().strftime("%H:%M"),
                project_id, ticket_id, ticket_title,
                description, duration
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        finally:
            self.disconnect()
    
    def get_entries(self, days=None):
        """Récupère les entrées."""
        try:
            self.connect()
            
            query = """
                SELECT 
                    e.id,
                    e.description,
                    e.duration,
                    e.date,
                    e.time,
                    e.ticket_title,
                    p.name as project_name,
                    t.ticket_number
                FROM entries e
                LEFT JOIN projects p ON e.project_id = p.id
                LEFT JOIN tickets t ON e.ticket_id = t.id
            """
            
            if days:
                query += f" WHERE date >= date('now', '-{days} days')"
            
            query += " ORDER BY date DESC, time DESC"
            
            self.cursor.execute(query)
            columns = [col[0] for col in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        finally:
            self.disconnect()
    
    def get_projects(self):
        """
        Récupère tous les projets.
        
        Returns:
            Liste des projets
        """
        self.connect()
        try:
            self.cursor.execute("SELECT * FROM projects ORDER BY name")
            return [dict(row) for row in self.cursor.fetchall()]
        finally:
            self.disconnect()
    
    def get_tickets(self, project_id):
        """
        Récupère les tickets d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des tickets
        """
        self.connect()
        try:
            self.cursor.execute("SELECT * FROM tickets WHERE project_id = ?", (project_id,))
            return [dict(row) for row in self.cursor.fetchall()]
        finally:
            self.disconnect()
    
    def get_entries_for_day(self, date):
        """
        Récupère les entrées pour un jour spécifique.
        
        Args:
            date: Date pour laquelle récupérer les entrées (datetime.date)
            
        Returns:
            Liste des entrées pour ce jour
        """
        self.connect()
        try:
            query = """
                SELECT * FROM entries 
                WHERE date = ?
                ORDER BY time DESC
            """
            self.cursor.execute(query, (date.isoformat(),))
            return [dict(row) for row in self.cursor.fetchall()]
        finally:
            self.disconnect()
    
    def get_entries_by_date_range(self, start_date, end_date):
        """
        Récupère les entrées dans une plage de dates avec les informations de projet.
        
        Args:
            start_date: Date de début (datetime.date)
            end_date: Date de fin (datetime.date)
            
        Returns:
            Liste des entrées avec les informations de projet
        """
        self.connect()
        try:
            query = """
                SELECT e.*, p.name as project_name, t.ticket_number, t.title as ticket_title
                FROM entries e
                LEFT JOIN projects p ON e.project_id = p.id
                LEFT JOIN tickets t ON e.ticket_id = t.id
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, time DESC
            """
            self.cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
            return [dict(row) for row in self.cursor.fetchall()]
        finally:
            self.disconnect()
    
    def get_entries_by_project(self, start_date, end_date):
        """
        Récupère les entrées groupées par projet dans une plage de dates.
        
        Args:
            start_date: Date de début (datetime.date)
            end_date: Date de fin (datetime.date)
            
        Returns:
            Dictionnaire avec les projets comme clés et leurs entrées comme valeurs
        """
        self.connect()
        try:
            query = """
                SELECT e.*, p.name as project_name, t.ticket_number, t.title as ticket_title,
                       date as entry_date
                FROM entries e
                LEFT JOIN projects p ON e.project_id = p.id
                LEFT JOIN tickets t ON e.ticket_id = t.id
                WHERE date BETWEEN ? AND ?
                ORDER BY COALESCE(p.name, ''), date DESC, time DESC
            """
            self.cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
            
            # Organise les résultats par projet
            entries_by_project = {}
            for row in self.cursor.fetchall():
                entry = dict(row)
                project_name = entry['project_name'] or 'Sans projet'
                if project_name not in entries_by_project:
                    entries_by_project[project_name] = []
                entries_by_project[project_name].append(entry)
            
            return entries_by_project
        finally:
            self.disconnect()

    def get_project_by_name(self, name):
        """
        Récupère un projet par son nom.
        
        Args:
            name: Nom du projet
            
        Returns:
            Dict avec les informations du projet ou None si pas trouvé
        """
        self.connect()
        try:
            self.cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        finally:
            self.disconnect()
    
    def get_project_suggestions(self):
        """Retourne la liste des noms de projets pour l'auto-complétion."""
        self.connect()
        try:
            self.cursor.execute("""
                SELECT DISTINCT name 
                FROM projects 
                WHERE name IS NOT NULL 
                ORDER BY name
            """)
            projects = [row[0] for row in self.cursor.fetchall()]
            return projects
        except Exception as e:
            print(f"Erreur lors de la récupération des suggestions de projets : {str(e)}")
            return []
        finally:
            self.disconnect()

    def get_ticket_suggestions(self):
        """Retourne la liste des numéros de tickets pour l'auto-complétion."""
        self.connect()
        try:
            self.cursor.execute("""
                SELECT DISTINCT ticket_number 
                FROM tickets 
                WHERE ticket_number IS NOT NULL 
                ORDER BY ticket_number
            """)
            tickets = [row[0] for row in self.cursor.fetchall()]
            return tickets
        except Exception as e:
            print(f"Erreur lors de la récupération des suggestions de tickets : {str(e)}")
            return []
        finally:
            self.disconnect()

    def save_setting(self, key, value):
        """Sauvegarde un paramètre."""
        try:
            self.connect()
            self.cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            """, (key, value))
            self.conn.commit()
        finally:
            self.disconnect()

    def get_setting(self, key, default=None):
        """Récupère un paramètre."""
        try:
            self.connect()
            self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = self.cursor.fetchone()
            return result[0] if result else default
        finally:
            self.disconnect()

    def get_unsynchronized_entries(self):
        """Récupère les entrées non synchronisées."""
        try:
            self.connect()
            self.cursor.execute("""
                SELECT 
                    e.id, 
                    e.date, 
                    e.time, 
                    e.project_id, 
                    e.ticket_id, 
                    e.description, 
                    e.duration, 
                    e.ticket_title,
                    p.name as project_name,
                    t.ticket_number as ticket_number
                FROM entries e
                LEFT JOIN projects p ON e.project_id = p.id
                LEFT JOIN tickets t ON e.ticket_id = t.id
                WHERE e.is_synced = 0
                ORDER BY e.date DESC, e.time DESC
            """)
            columns = [col[0] for col in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        finally:
            self.disconnect()

    def mark_entries_as_synced(self, entry_ids):
        """Marque les entrées comme synchronisées."""
        try:
            self.connect()
            self.cursor.executemany("""
                UPDATE entries
                SET is_synced = 1
                WHERE id = ?
            """, [(id,) for id in entry_ids])
            self.conn.commit()
        finally:
            self.disconnect()

    def get_last_ticket(self, project_id):
        """
        Récupère le dernier ticket utilisé pour un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Dict avec les informations du ticket ou None si pas de ticket
        """
        self.connect()
        try:
            query = """
                SELECT t.* 
                FROM tickets t
                JOIN entries e ON e.ticket_id = t.id
                WHERE t.project_id = ?
                ORDER BY e.date DESC, e.time DESC
                LIMIT 1
            """
            self.cursor.execute(query, (project_id,))
            row = self.cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'project_id': row[1],
                    'ticket_number': row[2],
                    'title': row[3],
                    'is_active': row[4]
                }
            return None
            
        except Exception as e:
            print(f"Erreur lors de la récupération du dernier ticket : {str(e)}")
            return None
        finally:
            self.disconnect()
    
    def get_project_tickets(self, project_id, include_inactive=False):
        """
        Récupère tous les tickets associés à un projet, triés par date d'utilisation.
        
        Args:
            project_id: ID du projet
            include_inactive: Si True, inclut aussi les tickets inactifs
            
        Returns:
            Liste des tickets, triée par date d'utilisation décroissante
        """
        self.connect()
        try:
            query = """
                SELECT DISTINCT t.ticket_number, t.title, COALESCE(t.is_active, 1) as is_active
                FROM tickets t
                LEFT JOIN entries e ON e.ticket_id = t.id
                WHERE t.project_id = ?
            """
            if not include_inactive:
                query += " AND COALESCE(t.is_active, 1) = 1"
            query += """
                GROUP BY t.ticket_number
                ORDER BY MAX(e.date || ' ' || e.time) DESC NULLS LAST
            """
            self.cursor.execute(query, (project_id,))
            return [{'ticket_number': row['ticket_number'], 'title': row['title'], 'is_active': row['is_active']} for row in self.cursor.fetchall()]
        finally:
            self.disconnect()

    def get_all_projects(self, include_inactive=False):
        """
        Récupère tous les projets avec leurs tickets.
        
        Args:
            include_inactive: Si True, inclut aussi les projets inactifs
            
        Returns:
            Liste des projets avec leurs tickets
        """
        self.connect()
        try:
            query = "SELECT id, name, is_active FROM projects"
            if not include_inactive:
                query += " WHERE is_active = 1"
            query += " ORDER BY name"
            
            self.cursor.execute(query)
            projects = []
            for row in self.cursor.fetchall():
                project = {
                    'id': row['id'],
                    'name': row['name'],
                    'is_active': row['is_active'],
                    'tickets': self.get_project_tickets(row['id'], include_inactive)
                }
                projects.append(project)
            return projects
        finally:
            self.disconnect()

    def toggle_project_active(self, project_id, is_active):
        """
        Active ou désactive un projet.
        
        Args:
            project_id: ID du projet
            is_active: True pour activer, False pour désactiver
        """
        self.connect()
        try:
            self.cursor.execute(
                "UPDATE projects SET is_active = ? WHERE id = ?",
                (1 if is_active else 0, project_id)
            )
            self.conn.commit()
        finally:
            self.disconnect()

    def toggle_ticket_active(self, project_id, ticket_number, is_active):
        """
        Active ou désactive un ticket.
        
        Args:
            project_id: ID du projet
            ticket_number: Numéro du ticket
            is_active: True pour activer, False pour désactiver
        """
        self.connect()
        try:
            self.cursor.execute(
                "UPDATE tickets SET is_active = ? WHERE project_id = ? AND ticket_number = ?",
                (1 if is_active else 0, project_id, ticket_number)
            )
            self.conn.commit()
        finally:
            self.disconnect()

    def get_entry_by_id(self, entry_id):
        """Récupère une entrée par son ID."""
        self.connect()
        try:
            self.cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        finally:
            self.disconnect()

    def get_total_minutes_for_day(self, date):
        """
        Calcule le total des minutes saisies pour une journée donnée.
        
        Args:
            date: Date pour laquelle calculer le total (format 'YYYY-MM-DD')
            
        Returns:
            Total des minutes saisies
        """
        self.connect()
        try:
            self.cursor.execute("""
                SELECT SUM(duration) as total_minutes
                FROM entries
                WHERE date = ?
            """, (date,))
            result = self.cursor.fetchone()
            return result['total_minutes'] or 0
        finally:
            self.disconnect()

    def get_jira_config(self):
        """
        Récupère la configuration Jira complète.
        
        Returns:
            dict: Configuration avec les clés jira_base_url, jira_email, et jira_token
        """
        return {
            'jira_base_url': self.get_setting('jira_base_url'),
            'jira_email': self.get_setting('jira_email'),
            'jira_token': self.get_setting('jira_token')
        }

    def get_sequential_time(self, date=None):
        """Retourne l'heure séquentielle pour une nouvelle entrée.
        
        L'heure retournée est basée sur le dernier événement de la journée :
        heure du dernier événement + sa durée
        
        Args:
            date: Date pour laquelle calculer l'heure (format: YYYY-MM-DD)
                 Si None, utilise la date du jour
                 
        Returns:
            str: Heure au format HH:mm
        """
        if not date:
            date = QDate.currentDate().toString("yyyy-MM-dd")
            
        # Récupère le dernier événement de la journée
        query = """
            SELECT time, duration 
            FROM entries 
            WHERE date = ? 
            ORDER BY time DESC
            LIMIT 1
        """
        self.connect()
        self.cursor.execute(query, (date,))
        last_entry = self.cursor.fetchone()
        
        if not last_entry:
            # Si pas d'événement ce jour, utilise l'heure de début configurée
            return self.get_setting('start_time')
            
        # Convertit l'heure du dernier événement en minutes depuis minuit
        last_time = last_entry['time']
        hours, minutes = map(int, last_time.split(':'))
        total_minutes = hours * 60 + minutes
        
        # Ajoute la durée du dernier événement
        total_minutes += last_entry['duration']
        
        # Convertit en heures:minutes
        new_hours = total_minutes // 60
        new_minutes = total_minutes % 60
        
        # Si on dépasse minuit, on reste à 23:59
        if new_hours >= 24:
            return "23:59"
            
        return f"{new_hours:02d}:{new_minutes:02d}"

    def get_recent_epic_feature_pairs(self, project_name, limit=10):
        """Récupère les paires Epic/Fonctionnalité récemment utilisées pour un projet.
        
        Args:
            project_name (str): Nom du projet
            limit (int): Nombre maximum de paires à retourner
            
        Returns:
            List[Tuple[str, str, str, str]]: Liste de tuples (epic_key, epic_name, feature_key, feature_name)
        """
        query = """
            SELECT e.key, e.name, f.key, f.name
            FROM epic_feature_pairs p
            JOIN epics e ON e.id = p.epic_id
            JOIN features f ON f.id = p.feature_id
            JOIN projects pr ON pr.id = p.project_id
            WHERE pr.name = ? AND e.visible = 1 AND f.visible = 1
            ORDER BY p.last_used DESC
            LIMIT ?
        """
        self.connect()
        self.cursor.execute(query, (project_name, limit))
        return self.cursor.fetchall()

    def add_epic(self, key, name, project_name):
        """Ajoute ou met à jour un epic.
        
        Args:
            key (str): Clé Jira de l'epic
            name (str): Nom de l'epic
            project_name (str): Nom du projet
        """
        project_id = self.get_project_id(project_name)
        if project_id:
            self.connect()
            self.cursor.execute("""
                INSERT OR REPLACE INTO epics (key, name, project_id, last_used)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, name, project_id))
            self.conn.commit()
            self.disconnect()

    def add_feature(self, key, name, project_name):
        """Ajoute ou met à jour une fonctionnalité.
        
        Args:
            key (str): Clé Jira de la fonctionnalité
            name (str): Nom de la fonctionnalité
            project_name (str): Nom du projet
        """
        project_id = self.get_project_id(project_name)
        if project_id:
            self.connect()
            self.cursor.execute("""
                INSERT OR REPLACE INTO features (key, name, project_id, last_used)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, name, project_id))
            self.conn.commit()
            self.disconnect()

    def add_epic_feature_pair(self, epic_key, feature_key, project_name):
        """Ajoute ou met à jour une paire Epic/Fonctionnalité.
        
        Args:
            epic_key (str): Clé Jira de l'epic
            feature_key (str): Clé Jira de la fonctionnalité
            project_name (str): Nom du projet
        """
        project_id = self.get_project_id(project_name)
        if project_id:
            # Récupérer les IDs des epic et feature
            epic_id = self.cursor.execute(
                "SELECT id FROM epics WHERE key = ? AND project_id = ?",
                (epic_key, project_id)
            ).fetchone()[0]
            
            feature_id = self.cursor.execute(
                "SELECT id FROM features WHERE key = ? AND project_id = ?",
                (feature_key, project_id)
            ).fetchone()[0]
            
            self.connect()
            self.cursor.execute("""
                INSERT OR REPLACE INTO epic_feature_pairs (epic_id, feature_id, project_id, last_used)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (epic_id, feature_id, project_id))
            self.conn.commit()
            self.disconnect()

    def set_epic_visibility(self, epic_key, project_name, visible):
        """Change la visibilité d'un epic.
        
        Args:
            epic_key (str): Clé Jira de l'epic
            project_name (str): Nom du projet
            visible (bool): True pour rendre visible, False pour cacher
        """
        project_id = self.get_project_id(project_name)
        if project_id:
            self.connect()
            self.cursor.execute("""
                UPDATE epics
                SET visible = ?
                WHERE key = ? AND project_id = ?
            """, (1 if visible else 0, epic_key, project_id))
            self.conn.commit()
            self.disconnect()

    def set_feature_visibility(self, feature_key, project_name, visible):
        """Change la visibilité d'une fonctionnalité.
        
        Args:
            feature_key (str): Clé Jira de la fonctionnalité
            project_name (str): Nom du projet
            visible (bool): True pour rendre visible, False pour cacher
        """
        project_id = self.get_project_id(project_name)
        if project_id:
            self.connect()
            self.cursor.execute("""
                UPDATE features
                SET visible = ?
                WHERE key = ? AND project_id = ?
            """, (1 if visible else 0, feature_key, project_id))
            self.conn.commit()
            self.disconnect()

    def get_project_id(self, project_name):
        """Récupère l'ID d'un projet par son nom."""
        self.connect()
        self.cursor.execute("SELECT id FROM projects WHERE name = ?", (project_name,))
        row = self.cursor.fetchone()
        project_id = row[0] if row else None
        self.disconnect()
        return project_id

    def get_all_subtasks(self):
        """Récupère tous les tickets de la table jira_subtasks."""
        self.connect()
        self.cursor.execute("""
            SELECT ticket_key, title, path
            FROM jira_subtasks
            ORDER BY ticket_key
        """)
        
        rows = self.cursor.fetchall()
        result = [
            {
                'ticket_number': row[0],  # ticket_key dans la base
                'title': row[1],
                'path': row[2]
            }
            for row in rows
        ]
        self.disconnect()
        return result