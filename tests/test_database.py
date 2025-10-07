"""Unit tests for Database operations"""

import pytest
import tempfile
from pathlib import Path
from src.database.db import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        yield db
        db.close()


def test_create_run(temp_db):
    """Test creating a run"""
    temp_db.create_run("test_run_1", "2025-09-23", "2025-09-29", ["user1@example.com"])
    
    # Verify run was created
    cursor = temp_db.conn.cursor()
    cursor.execute("SELECT * FROM runs WHERE run_id = ?", ("test_run_1",))
    row = cursor.fetchone()
    
    assert row is not None
    assert row['run_id'] == "test_run_1"
    assert row['start_date'] == "2025-09-23"
    assert row['end_date'] == "2025-09-29"
    assert row['status'] == "in_progress"


def test_upsert_time_entries(temp_db):
    """Test upserting time entries"""
    temp_db.create_run("test_run_2", "2025-09-23", "2025-09-29", [])
    
    entries = [
        {
            'id': 1001,
            'workspace_id': 123,
            'user_id': 456,
            'username': 'John Doe',
            'user_email': 'john@example.com',
            'description': 'Test task #1234 [Backend] [Bug] [Project]',
            'start': '2025-09-23T09:00:00Z',
            'stop': '2025-09-23T10:00:00Z',
            'duration': 3600,
            'tags': [],
            'project_id': 789,
            'project_name': 'TestProject'
        }
    ]
    
    count = temp_db.upsert_time_entries("test_run_2", entries)
    
    assert count == 1
    
    # Verify entry was inserted
    cursor = temp_db.conn.cursor()
    cursor.execute("SELECT * FROM toggl_time_entries WHERE toggl_id = ?", (1001,))
    row = cursor.fetchone()
    
    assert row is not None
    assert row['user_email'] == 'john@example.com'
    assert row['duration'] == 3600


def test_upsert_processed_entries(temp_db):
    """Test upserting processed entries"""
    temp_db.create_run("test_run_3", "2025-09-23", "2025-09-29", [])
    
    processed = [
        {
            'user_email': 'john@example.com',
            'description_clean': 'Test task',
            'entity_id': '1234',
            'entity_database': 'Backend',
            'entity_type': 'Bug',
            'project': 'Project',
            'is_matched': True,
            'total_duration': 3600,
            'entry_count': 1
        }
    ]
    
    count = temp_db.upsert_processed_entries("test_run_3", processed)
    
    assert count == 1
    
    # Verify entry was inserted
    entries = temp_db.get_processed_entries_by_run("test_run_3")
    
    assert len(entries) == 1
    assert entries[0]['entity_id'] == '1234'
    assert entries[0]['is_matched'] == 1  # SQLite returns as int

