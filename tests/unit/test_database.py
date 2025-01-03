import pytest
import sqlite3
from datetime import datetime, timedelta
import os
from src.utils.database import Database

@pytest.fixture
def test_db():
    """Fixture qui fournit une base de données de test."""
    db_path = "data/test_logtracker.db"
    db = Database(db_path)
    yield db
    # Nettoyage après les tests
    if os.path.exists(db_path):
        os.remove(db_path)

def test_create_tables(test_db):
    """Vérifie que les tables sont créées correctement."""
    test_db.connect()
    cursor = test_db.conn.cursor()
    
    # Vérifie l'existence des tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    
    assert "projects" in tables
    assert "tickets" in tables
    assert "entries" in tables
    
    test_db.disconnect()

def test_add_project(test_db):
    """Teste l'ajout d'un projet."""
    project_name = "Test Project"
    jira_key = "TEST"
    
    # Ajoute un projet
    project_id = test_db.add_project(project_name, jira_key)
    assert project_id is not None
    
    # Vérifie que le projet existe
    projects = test_db.get_projects()
    assert len(projects) == 1
    assert projects[0]["name"] == project_name
    assert projects[0]["jira_key"] == jira_key

def test_add_ticket(test_db):
    """Teste l'ajout d'un ticket."""
    # Crée d'abord un projet
    project_id = test_db.add_project("Test Project")
    
    # Ajoute un ticket
    ticket_number = "TEST-123"
    description = "Test ticket"
    ticket_id = test_db.add_ticket(project_id, ticket_number, description)
    
    assert ticket_id is not None
    
    # Vérifie que le ticket existe
    tickets = test_db.get_tickets(project_id)
    assert len(tickets) == 1
    assert tickets[0]["ticket_number"] == ticket_number
    assert tickets[0]["description"] == description

def test_add_entry(test_db):
    """Teste l'ajout d'une entrée de journal."""
    # Crée les données nécessaires
    project_id = test_db.add_project("Test Project")
    ticket_id = test_db.add_ticket(project_id, "TEST-123")
    
    # Ajoute une entrée
    description = "Test entry"
    duration = 30
    entry_id = test_db.add_entry(description, project_id, ticket_id, duration)
    
    assert entry_id is not None
    
    # Vérifie que l'entrée existe
    entries = test_db.get_entries()
    assert len(entries) == 1
    assert entries[0]["description"] == description
    assert entries[0]["duration"] == duration
    assert entries[0]["project_id"] == project_id
    assert entries[0]["ticket_id"] == ticket_id

def test_get_entries_with_date_filter(test_db):
    """Teste la récupération des entrées avec filtre de date."""
    # Ajoute quelques entrées
    test_db.add_entry("Entry 1")
    test_db.add_entry("Entry 2")
    
    # Récupère les entrées d'aujourd'hui
    today = datetime.now().date()
    start_date = datetime.combine(today, datetime.min.time())
    end_date = datetime.combine(today, datetime.max.time())
    
    entries = test_db.get_entries(start_date, end_date)
    assert len(entries) == 2

def test_unique_project_name(test_db):
    """Vérifie qu'on ne peut pas avoir deux projets avec le même nom."""
    test_db.add_project("Test Project")
    
    with pytest.raises(sqlite3.IntegrityError):
        test_db.add_project("Test Project")
