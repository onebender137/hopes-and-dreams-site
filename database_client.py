import sqlite3
import os
import json
from datetime import datetime
from contextlib import contextmanager

DB_NAME = "syndicate_memory.db"

class SyndicateDatabase:
    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for SQLite connections to ensure safety and performance."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes the SQLite database and creates necessary tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table for posted topics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posted_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    posted_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Table for replied comments
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS replied_comments (
                    comment_id TEXT PRIMARY KEY,
                    replied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_posted_topic(self, topic):
        """Records a new posted topic."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO posted_topics (topic) VALUES (?)', (topic,))
            conn.commit()

    def get_recent_topics(self, limit=50):
        """Retrieves the most recently posted topics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT topic FROM posted_topics ORDER BY posted_at DESC LIMIT ?', (limit,))
            return [row[0] for row in cursor.fetchall()]

    def add_replied_comment(self, comment_id):
        """Records a comment ID that has been replied to."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO replied_comments (comment_id) VALUES (?)', (comment_id,))
                conn.commit()
            except sqlite3.IntegrityError:
                pass # Already exists

    def is_comment_replied(self, comment_id):
        """Checks if a comment ID has already been replied to."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM replied_comments WHERE comment_id = ?', (comment_id,))
            return cursor.fetchone() is not None

    def get_all_replied_comments(self):
        """Retrieves all replied comment IDs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT comment_id FROM replied_comments')
            return set(row[0] for row in cursor.fetchall())

    def migrate_from_json(self, posted_json_path, replied_json_path):
        """Migrates data from old JSON files to SQLite."""
        migrated = False

        # Migrate posted topics
        if os.path.exists(posted_json_path):
            print(f"Migrating posted topics from {posted_json_path}...")
            try:
                with open(posted_json_path, 'r') as f:
                    topics = json.load(f)
                    for topic in topics:
                        self.add_posted_topic(topic)
                migrated = True
            except Exception as e:
                print(f"Error migrating posted topics: {e}")

        # Migrate replied comments
        if os.path.exists(replied_json_path):
            print(f"Migrating replied comments from {replied_json_path}...")
            try:
                with open(replied_json_path, 'r') as f:
                    comment_ids = json.load(f)
                    for cid in comment_ids:
                        self.add_replied_comment(cid)
                migrated = True
            except Exception as e:
                print(f"Error migrating replied comments: {e}")

        return migrated

if __name__ == "__main__":
    # Quick standalone test
    db = SyndicateDatabase("test_syndicate.db")
    db.add_posted_topic("Huperzine-A")
    print("Recent topics:", db.get_recent_topics())
    db.add_replied_comment("12345")
    print("Is 12345 replied?", db.is_comment_replied("12345"))
    os.remove("test_syndicate.db")
