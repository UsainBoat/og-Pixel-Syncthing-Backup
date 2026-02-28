import sqlite3
import os

class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def connect(self):
        """Deprecated: Connection is now established in __init__."""
        pass

    def _create_table(self):
        """Creates the necessary table if it doesn't exist."""
        # We track filepath to ensure we don't copy the exact same file again.
        # Note: If a file is renamed in source, it will be treated as a new file.
        # This is generally desired behavior for backup consistency.
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS copied_files (
                filepath TEXT PRIMARY KEY,
                copied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def is_copied(self, filepath):
        """Checks if a file has already been logged as copied."""
        self.cursor.execute('SELECT 1 FROM copied_files WHERE filepath = ?', (filepath,))
        return self.cursor.fetchone() is not None

    def log_copy(self, filepath):
        """Logs a file as copied."""
        try:
            self.cursor.execute('INSERT INTO copied_files (filepath) VALUES (?)', (filepath,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Already exists, which is fine
            pass

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
