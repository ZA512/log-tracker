import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import os

class Database:
    """Gestionnaire de la base de données SQLite."""
    
    def __init__(self):
        """Initialise la connexion à la base de données."""
        self.db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, 'logtracker.db')
        self.conn = None
        self.create_tables()
    
    def connect(self):
        """Établit une connexion à la base de données."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
    
    def disconnect(self):
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def create_tables(self):
        """Crée les tables de la base de données."""
        try:
            self.connect()
            cursor = self.conn.cursor()

            # Table des projets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            """)

            # Table des tickets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    ticket_number TEXT NOT NULL,
                    title TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id),
                    UNIQUE(project_id, ticket_number)
                )
            """)

            # Table des entrées
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    ticket_id INTEGER,
                    description TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    is_synced INTEGER DEFAULT 0,
                    ticket_title TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id),
                    FOREIGN KEY (ticket_id) REFERENCES tickets (id)
                )
            """)

            # Table des paramètres
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Ajout des paramètres par défaut
            cursor.execute("""
                INSERT OR IGNORE INTO settings (key, value) VALUES 
                    ('jira_base_url', NULL),
                    ('jira_token', NULL),
                    ('jira_email', NULL),
                    ('daily_hours', '8')
            """)

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
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO projects (name) VALUES (?)", (name,))
            self.conn.commit()
            return cursor.lastrowid
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
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO tickets (project_id, ticket_number, title)
                VALUES (?, ?, ?)
            """, (project_id, ticket_number, title))
            self.conn.commit()
            return cursor.lastrowid
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
            cursor = self.conn.cursor()
            cursor.execute("UPDATE tickets SET title = ? WHERE id = ?", (title, ticket_id))
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
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, ticket_number, title
                FROM tickets
                WHERE project_id = ? AND ticket_number = ?
            """, (project_id, ticket_number))
            return cursor.fetchone()
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
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, ticket_number, title
                FROM tickets
                WHERE project_id = ?
                ORDER BY ticket_number DESC
            """, (project_id,))
            return cursor.fetchall()
        finally:
            self.disconnect()
    
    def add_entry(self, description, project_id=None, ticket_id=None, duration=60, ticket_title=None, date=None, time=None):
        """Ajoute une nouvelle entrée."""
        try:
            self.connect()
            cursor = self.conn.cursor()

            # Si date ou heure non fournies, utilise la date et l'heure actuelles
            if not date or not time:
                now = datetime.now()
                date = now.strftime("%Y-%m-%d")
                time = now.strftime("%H:%M")

            cursor.execute("""
                INSERT INTO entries (project_id, ticket_id, description, duration, date, time, ticket_title)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (project_id, ticket_id, description, duration, date, time, ticket_title))
            
            self.conn.commit()
            return cursor.lastrowid
        finally:
            self.disconnect()
    
    def get_entries(self, days=None):
        """Récupère les entrées."""
        try:
            self.connect()
            cursor = self.conn.cursor()

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

            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
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
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
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
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tickets WHERE project_id = ?", (project_id,))
            return [dict(row) for row in cursor.fetchall()]
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
            cursor = self.conn.cursor()
            query = """
                SELECT * FROM entries 
                WHERE date = ?
                ORDER BY time DESC
            """
            cursor.execute(query, (date.isoformat(),))
            return [dict(row) for row in cursor.fetchall()]
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
            cursor = self.conn.cursor()
            query = """
                SELECT e.*, p.name as project_name, t.ticket_number, t.title as ticket_title
                FROM entries e
                LEFT JOIN projects p ON e.project_id = p.id
                LEFT JOIN tickets t ON e.ticket_id = t.id
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, time DESC
            """
            cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
            return [dict(row) for row in cursor.fetchall()]
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
            cursor = self.conn.cursor()
            query = """
                SELECT e.*, p.name as project_name, t.ticket_number, t.title as ticket_title,
                       date as entry_date
                FROM entries e
                LEFT JOIN projects p ON e.project_id = p.id
                LEFT JOIN tickets t ON e.ticket_id = t.id
                WHERE date BETWEEN ? AND ?
                ORDER BY COALESCE(p.name, ''), date DESC, time DESC
            """
            cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
            
            # Organise les résultats par projet
            entries_by_project = {}
            for row in cursor.fetchall():
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
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            self.disconnect()
    
    def get_project_suggestions(self):
        """Retourne la liste des noms de projets pour l'auto-complétion."""
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT DISTINCT name 
                FROM projects 
                WHERE name IS NOT NULL 
                ORDER BY name
            """)
            projects = [row[0] for row in cursor.fetchall()]
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
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT DISTINCT ticket_number 
                FROM tickets 
                WHERE ticket_number IS NOT NULL 
                ORDER BY ticket_number
            """)
            tickets = [row[0] for row in cursor.fetchall()]
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
            cursor = self.conn.cursor()
            cursor.execute("""
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
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else default
        finally:
            self.disconnect()

    def get_unsynchronized_entries(self):
        """Récupère les entrées non synchronisées."""
        try:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("""
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
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            self.disconnect()

    def mark_entries_as_synced(self, entry_ids):
        """Marque les entrées comme synchronisées."""
        try:
            self.connect()
            cursor = self.conn.cursor()
            cursor.executemany("""
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
            cursor = self.conn.cursor()
            query = """
                SELECT t.* 
                FROM tickets t
                JOIN entries e ON e.ticket_id = t.id
                WHERE t.project_id = ?
                ORDER BY e.date DESC, e.time DESC
                LIMIT 1
            """
            cursor.execute(query, (project_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'project_id': row[1],
                    'ticket_number': row[2],
                    'title': row[3]
                }
            return None
            
        except Exception as e:
            print(f"Erreur lors de la récupération du dernier ticket : {str(e)}")
            return None
        finally:
            self.disconnect()
    
    def get_project_tickets(self, project_id):
        """
        Récupère tous les tickets associés à un projet, triés par date d'utilisation.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des tickets, triée par date d'utilisation décroissante
        """
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT DISTINCT t.ticket_number, t.title
                FROM tickets t
                LEFT JOIN entries e ON e.ticket_id = t.id
                WHERE t.project_id = ?
                GROUP BY t.ticket_number
                ORDER BY MAX(e.date || ' ' || e.time) DESC NULLS LAST
            """, (project_id,))
            return [{'ticket_number': row['ticket_number'], 'title': row['title']} for row in cursor.fetchall()]
        finally:
            self.disconnect()
            
    def get_entry_by_id(self, entry_id):
        """Récupère une entrée par son ID."""
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
            row = cursor.fetchone()
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
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT SUM(duration) as total_minutes
                FROM entries
                WHERE date = ?
            """, (date,))
            result = cursor.fetchone()
            return result['total_minutes'] or 0
        finally:
            self.disconnect()