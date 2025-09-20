# db_manager.py
import os
import psycopg2
import psycopg2.extras

class DBManager:
    def __init__(self):
        self.conn = None # <-- Don't connect on initialization

    def _ensure_connection(self):
        """Checks if a connection exists and creates one if not."""
        if self.conn is None or self.conn.closed:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL environment variable is not set.")
            self.conn = psycopg2.connect(db_url)

    def execute(self, sql, params=None):
        self._ensure_connection() # <-- Connect just-in-time
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            self.conn.commit()

    def query_one(self, sql, params=None):
        self._ensure_connection() # <-- Connect just-in-time
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def query_all(self, sql, params=None):
        self._ensure_connection() # <-- Connect just-in-time
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
