import pytest
from datetime import datetime
from src.core.models.entry import Entry

def test_entry_creation():
    """Test la création d'une entrée de journal basique"""
    description = "Test de la fonctionnalité X"
    entry = Entry(description=description)
    
    assert entry.description == description
    assert isinstance(entry.timestamp, datetime)
    assert entry.project_id is None
    assert entry.ticket_id is None
    assert entry.duration is None
    assert entry.synced_to_jira is False

def test_entry_creation_with_all_fields():
    """Test la création d'une entrée de journal avec tous les champs"""
    description = "Test complet"
    project_id = 1
    ticket_id = 100
    duration = 30
    
    entry = Entry(
        description=description,
        project_id=project_id,
        ticket_id=ticket_id,
        duration=duration
    )
    
    assert entry.description == description
    assert entry.project_id == project_id
    assert entry.ticket_id == ticket_id
    assert entry.duration == duration
    assert entry.synced_to_jira is False

def test_entry_invalid_duration():
    """Test que la durée ne peut pas être négative"""
    with pytest.raises(ValueError):
        Entry(description="Test", duration=-1)

def test_entry_empty_description():
    """Test qu'une description vide n'est pas autorisée"""
    with pytest.raises(ValueError):
        Entry(description="")
