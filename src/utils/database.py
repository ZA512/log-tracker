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
        """Crée les tables si elles n'existent pas."""
        self.connect()
        try:
            cursor = self.conn.cursor()
            
            # Table des projets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            
            # Table des tickets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    ticket_number TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    UNIQUE(project_id, ticket_number)
                )
            """)
            
            # Table des entrées
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    project_id INTEGER,
                    ticket_id INTEGER,
                    duration INTEGER,
                    sync_status INTEGER DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
                )
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
    
    def add_ticket(self, project_id, ticket_number):
        """
        Ajoute un ticket.
        
        Args:
            project_id: ID du projet
            ticket_number: Numéro du ticket
            
        Returns:
            ID du ticket
        """
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO tickets (project_id, ticket_number) VALUES (?, ?)",
                (project_id, ticket_number)
            )
            self.conn.commit()
            return cursor.lastrowid
        finally:
            self.disconnect()
    
    def add_entry(self, description, project_id=None, ticket_id=None, duration=None):
        """
        Ajoute une entrée.
        
        Args:
            description: Description de l'entrée
            project_id: ID du projet (optionnel)
            ticket_id: ID du ticket (optionnel)
            duration: Durée en minutes (optionnel)
        """
        self.connect()
        try:
            cursor = self.conn.cursor()
            
            # Si un projet est spécifié par son nom, on le crée ou on le récupère
            if project_id and isinstance(project_id, str):
                cursor.execute("SELECT id FROM projects WHERE name = ?", (project_id,))
                row = cursor.fetchone()
                if row:
                    project_id = row[0]
                else:
                    cursor.execute("INSERT INTO projects (name) VALUES (?)", (project_id,))
                    project_id = cursor.lastrowid
            
            # Si un ticket est spécifié, on le crée ou on le récupère
            if ticket_id and project_id and isinstance(ticket_id, str):
                cursor.execute(
                    "SELECT id FROM tickets WHERE project_id = ? AND ticket_number = ?",
                    (project_id, ticket_id)
                )
                row = cursor.fetchone()
                if row:
                    ticket_id = row[0]
                else:
                    cursor.execute(
                        "INSERT INTO tickets (project_id, ticket_number) VALUES (?, ?)",
                        (project_id, ticket_id)
                    )
                    ticket_id = cursor.lastrowid
            
            # Ajoute l'entrée
            cursor.execute(
                """
                INSERT INTO entries 
                (description, timestamp, project_id, ticket_id, duration)
                VALUES (?, datetime('now', 'localtime'), ?, ?, ?)
                """,
                (description, project_id, ticket_id, duration)
            )
            self.conn.commit()
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
    
    def get_entries(self, start_date=None, end_date=None):
        """
        Récupère les entrées dans une plage de dates.
        
        Args:
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
            
        Returns:
            Liste des entrées
        """
        self.connect()
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM entries"
            params = []
            
            if start_date or end_date:
                query += " WHERE"
                if start_date:
                    query += " timestamp >= ?"
                    params.append(start_date.isoformat())
                if end_date:
                    if start_date:
                        query += " AND"
                    query += " timestamp <= ?"
                    params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
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
            query = """
                SELECT DISTINCT t.ticket_number, MAX(e.timestamp) as last_used
                FROM tickets t
                LEFT JOIN entries e ON e.ticket_id = t.id
                WHERE t.project_id = ?
                GROUP BY t.ticket_number
                ORDER BY last_used DESC NULLS LAST
            """
            cursor.execute(query, (project_id,))
            return [row[0] for row in cursor.fetchall()]
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
                ORDER BY e.timestamp DESC
                LIMIT 1
            """
            cursor.execute(query, (project_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'project_id': row[1],
                    'ticket_number': row[2]
                }
            return None
            
        except Exception as e:
            print(f"Erreur lors de la récupération du dernier ticket : {str(e)}")
            return None
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
                WHERE date(timestamp) = date(?)
                ORDER BY timestamp DESC
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
                SELECT e.*, p.name as project_name, t.ticket_number
                FROM entries e
                LEFT JOIN projects p ON e.project_id = p.id
                LEFT JOIN tickets t ON e.ticket_id = t.id
                WHERE date(e.timestamp) BETWEEN date(?) AND date(?)
                ORDER BY e.timestamp DESC
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
                SELECT e.*, p.name as project_name, t.ticket_number,
                       date(e.timestamp) as entry_date
                FROM entries e
                LEFT JOIN projects p ON e.project_id = p.id
                LEFT JOIN tickets t ON e.ticket_id = t.id
                WHERE date(e.timestamp) BETWEEN date(?) AND date(?)
                ORDER BY COALESCE(p.name, ''), e.timestamp
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
