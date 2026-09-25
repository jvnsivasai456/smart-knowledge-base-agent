import sqlite3
from typing import Optional, List, Dict
from datetime import datetime, timezone

class MetadataStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize the SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    source_id TEXT PRIMARY KEY,
                    source_type TEXT,
                    file_hash TEXT,
                    upload_time TEXT,
                    last_indexed TEXT
                )
            ''')
            conn.commit()
            
    def upsert_file_record(self, source_id: str, source_type: str, file_hash: str):
        """Insert or update a file record."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO files (source_id, source_type, file_hash, upload_time, last_indexed)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    file_hash=excluded.file_hash,
                    last_indexed=excluded.last_indexed
            ''', (source_id, source_type, file_hash, now, now))
            conn.commit()
            
    def get_file_record(self, source_id: str) -> Optional[Dict]:
        """Get a file record by source_id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM files WHERE source_id = ?', (source_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def delete_file_record(self, source_id: str):
        """Delete a file record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM files WHERE source_id = ?', (source_id,))
            conn.commit()
            
    def get_all_files(self) -> List[Dict]:
        """Get all tracked file records."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM files')
            return [dict(row) for row in cursor.fetchall()]
