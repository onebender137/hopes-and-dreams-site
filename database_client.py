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
                    slot TEXT,
                    posted_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Migration: Ensure 'slot' column exists in posted_topics
            cursor.execute("PRAGMA table_info(posted_topics)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'slot' not in columns:
                cursor.execute('ALTER TABLE posted_topics ADD COLUMN slot TEXT')

            # Table for replied comments
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS replied_comments (
                    comment_id TEXT PRIMARY KEY,
                    replied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Table for scheduled future topics (manual queue)
            # status: 'pending' (waiting), 'used' (consumed by post), 'cancelled'
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scheduled_date TEXT NOT NULL,
                    slot TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    used_at DATETIME,
                    UNIQUE(scheduled_date, slot)
                )
            ''')
            conn.commit()

    def add_posted_topic(self, topic, slot=None):
        """Records a new posted topic."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO posted_topics (topic, slot) VALUES (?, ?)', (topic, slot))
            conn.commit()

    def is_slot_posted(self, date_str, slot):
        """Checks if a specific slot has already been posted on a given date."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # SQLite CURRENT_TIMESTAMP is UTC. We'll use date(posted_at) for comparison.
            cursor.execute('''
                SELECT 1 FROM posted_topics
                WHERE date(posted_at, 'localtime') = ? AND slot = ?
            ''', (date_str, slot))
            return cursor.fetchone() is not None

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

    # ===== SCHEDULED TOPIC QUEUE =====
    # Manual queue for pre-planning days/weeks of content
    # Bot reads from this queue FIRST when it's time to post.

    def schedule_topic(self, scheduled_date, slot, topic):
        """
        Queues a topic for a specific date+slot. Replaces any existing entry for that slot.
        scheduled_date: 'YYYY-MM-DD'
        slot: '07:00' / '12:00' / '15:00'
        topic: free-form topic string
        Returns True on success.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # UPSERT — if already scheduled for this slot, replace it
            cursor.execute('''
                INSERT INTO scheduled_topics (scheduled_date, slot, topic, status)
                VALUES (?, ?, ?, 'pending')
                ON CONFLICT(scheduled_date, slot)
                DO UPDATE SET topic=excluded.topic, status='pending', created_at=CURRENT_TIMESTAMP, used_at=NULL
            ''', (scheduled_date, slot, topic))
            conn.commit()
            return cursor.rowcount > 0

    def get_scheduled_topic(self, scheduled_date, slot):
        """
        Returns the pending topic for a date+slot, or None if nothing scheduled.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT topic FROM scheduled_topics
                WHERE scheduled_date=? AND slot=? AND status='pending'
            ''', (scheduled_date, slot))
            row = cursor.fetchone()
            return row[0] if row else None

    def mark_scheduled_used(self, scheduled_date, slot):
        """
        Marks a scheduled topic as consumed (after the bot uses it).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE scheduled_topics
                SET status='used', used_at=CURRENT_TIMESTAMP
                WHERE scheduled_date=? AND slot=? AND status='pending'
            ''', (scheduled_date, slot))
            conn.commit()

    def list_scheduled_upcoming(self, from_date=None, limit=50):
        """
        Returns all pending scheduled topics from a given date forward.
        If from_date is None, returns from today.
        Returns list of (date, slot, topic) tuples ordered chronologically.
        """
        from datetime import datetime as _dt
        if from_date is None:
            from_date = _dt.now().strftime('%Y-%m-%d')
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT scheduled_date, slot, topic FROM scheduled_topics
                WHERE scheduled_date >= ? AND status='pending'
                ORDER BY scheduled_date, slot
                LIMIT ?
            ''', (from_date, limit))
            return cursor.fetchall()

    def unschedule_topic(self, scheduled_date, slot):
        """
        Cancels (removes) a scheduled topic for a date+slot.
        Returns True if anything was deleted.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM scheduled_topics
                WHERE scheduled_date=? AND slot=? AND status='pending'
            ''', (scheduled_date, slot))
            conn.commit()
            return cursor.rowcount > 0

    def clear_scheduled_for_date(self, scheduled_date):
        """Removes all pending scheduled topics for a given date. Useful for re-planning."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM scheduled_topics
                WHERE scheduled_date=? AND status='pending'
            ''', (scheduled_date,))
            conn.commit()
            return cursor.rowcount

if __name__ == "__main__":
    # Quick standalone test
    db = SyndicateDatabase("test_syndicate.db")
    db.add_posted_topic("Huperzine-A")
    print("Recent topics:", db.get_recent_topics())
    db.add_replied_comment("12345")
    print("Is 12345 replied?", db.is_comment_replied("12345"))
    os.remove("test_syndicate.db")
