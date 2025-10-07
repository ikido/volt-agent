"""Database operations for SQLite cache"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    """SQLite database for caching Toggl data and processed results"""
    
    def __init__(self, db_path: str = "./data/toggl_cache.db"):
        """Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._connect()
        self._initialize_schema()
    
    def _connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")
    
    def _initialize_schema(self):
        """Initialize database schema from schema.sql"""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        self.conn.executescript(schema_sql)
        self.conn.commit()
        logger.info("Database schema initialized")
    
    def create_run(self, run_id: str, start_date: str, end_date: str, 
                   user_emails: List[str]) -> None:
        """Create a new run record
        
        Args:
            run_id: Unique run identifier
            start_date: Report start date
            end_date: Report end date
            user_emails: List of user emails
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO runs (run_id, timestamp, start_date, end_date, user_emails, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            datetime.now().isoformat(),
            start_date,
            end_date,
            json.dumps(user_emails),
            'in_progress'
        ))
        self.conn.commit()
        logger.info(f"Created run: {run_id}")
    
    def update_run_status(self, run_id: str, status: str, total_entries: Optional[int] = None):
        """Update run status
        
        Args:
            run_id: Run identifier
            status: New status ('in_progress', 'completed', 'failed')
            total_entries: Optional total entry count
        """
        cursor = self.conn.cursor()
        if total_entries is not None:
            cursor.execute("""
                UPDATE runs SET status = ?, total_entries = ? WHERE run_id = ?
            """, (status, total_entries, run_id))
        else:
            cursor.execute("""
                UPDATE runs SET status = ? WHERE run_id = ?
            """, (status, run_id))
        self.conn.commit()
        logger.info(f"Updated run {run_id} status to: {status}")
    
    def upsert_time_entries(self, run_id: str, entries: List[Dict[str, Any]]) -> int:
        """Upsert time entries from Toggl
        
        Args:
            run_id: Current run identifier
            entries: List of time entry dictionaries
            
        Returns:
            Number of entries processed
        """
        cursor = self.conn.cursor()
        count = 0
        
        for entry in entries:
            # Convert tags to JSON string if it's a list
            tags = entry.get('tags', [])
            if isinstance(tags, list):
                tags = json.dumps(tags)
            
            cursor.execute("""
                INSERT INTO toggl_time_entries 
                (toggl_id, run_id, workspace_id, user_id, username, user_email, 
                 description, start_time, stop_time, duration, tags, project_id, project_name, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(toggl_id) DO UPDATE SET
                    run_id = excluded.run_id,
                    workspace_id = excluded.workspace_id,
                    user_id = excluded.user_id,
                    username = excluded.username,
                    user_email = excluded.user_email,
                    description = excluded.description,
                    start_time = excluded.start_time,
                    stop_time = excluded.stop_time,
                    duration = excluded.duration,
                    tags = excluded.tags,
                    project_id = excluded.project_id,
                    project_name = excluded.project_name,
                    updated_at = excluded.updated_at
            """, (
                entry.get('id'),
                run_id,
                entry.get('workspace_id'),
                entry.get('user_id'),
                entry.get('username'),
                entry.get('user_email'),
                entry.get('description', ''),
                entry.get('start'),
                entry.get('stop'),
                entry.get('duration', 0),
                tags,
                entry.get('project_id'),
                entry.get('project_name'),
                datetime.now().isoformat()
            ))
            count += 1
        
        self.conn.commit()
        logger.info(f"Upserted {count} time entries for run {run_id}")
        return count
    
    def upsert_processed_entries(self, run_id: str, entries: List[Dict[str, Any]]) -> int:
        """Upsert processed time entries
        
        Args:
            run_id: Current run identifier
            entries: List of processed entry dictionaries
            
        Returns:
            Number of entries processed
        """
        cursor = self.conn.cursor()
        count = 0
        
        for entry in entries:
            cursor.execute("""
                INSERT INTO processed_time_entries 
                (run_id, user_email, description_clean, entity_id, entity_database, 
                 entity_type, project, is_matched, total_duration, entry_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id, user_email, description_clean, entity_id, entity_database, entity_type, project) 
                DO UPDATE SET
                    total_duration = excluded.total_duration,
                    entry_count = excluded.entry_count,
                    updated_at = excluded.updated_at
            """, (
                run_id,
                entry['user_email'],
                entry['description_clean'],
                entry.get('entity_id'),
                entry.get('entity_database'),
                entry.get('entity_type'),
                entry.get('project'),
                entry['is_matched'],
                entry['total_duration'],
                entry['entry_count'],
                datetime.now().isoformat()
            ))
            count += 1
        
        self.conn.commit()
        logger.info(f"Upserted {count} processed entries for run {run_id}")
        return count
    
    def get_time_entries_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all time entries for a run
        
        Args:
            run_id: Run identifier
            
        Returns:
            List of time entry dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM toggl_time_entries WHERE run_id = ?
            ORDER BY start_time
        """, (run_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_processed_entries_by_run(self, run_id: str, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get processed entries for a run, optionally filtered by user
        
        Args:
            run_id: Run identifier
            user_email: Optional user email filter
            
        Returns:
            List of processed entry dictionaries
        """
        cursor = self.conn.cursor()
        
        if user_email:
            cursor.execute("""
                SELECT * FROM processed_time_entries 
                WHERE run_id = ? AND user_email = ?
                ORDER BY total_duration DESC
            """, (run_id, user_email))
        else:
            cursor.execute("""
                SELECT * FROM processed_time_entries 
                WHERE run_id = ?
                ORDER BY user_email, total_duration DESC
            """, (run_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def save_report(self, run_id: str, report_type: str, content: str, 
                   file_path: str, user_email: Optional[str] = None):
        """Save generated report
        
        Args:
            run_id: Run identifier
            report_type: Type of report ('individual', 'team')
            content: Markdown content
            file_path: Path to saved file
            user_email: Optional user email for individual reports
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO reports (run_id, report_type, user_email, content, file_path)
            VALUES (?, ?, ?, ?, ?)
        """, (run_id, report_type, user_email, content, file_path))
        self.conn.commit()
        logger.info(f"Saved {report_type} report for run {run_id}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

