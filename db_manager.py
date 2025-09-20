# db_manager.py
import os
import psycopg2
import psycopg2.extras

class DBManager:
    """A helper class to manage connections and queries to the PostgreSQL database."""
    def __init__(self):
        self.conn = self._get_connection()

    def _get_connection(self):
        """Establishes the database connection using the DATABASE_URL."""
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is not set.")
        try:
            return psycopg2.connect(db_url)
        except psycopg2.OperationalError as e:
            print(f"Error connecting to the database: {e}")
            raise

    def execute(self, sql, params=None):
        """Executes a SQL command like INSERT, UPDATE, or DELETE."""
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            self.conn.commit()

    def query_one(self, sql, params=None):
        """Executes a SELECT query and returns the first result as a dictionary."""
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    # --- ADD THIS NEW METHOD ---
    def query_all(self, sql, params=None):
        """Executes a SELECT query and returns all results as a list of dictionaries."""
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def __del__(self):
        """Ensures the connection is closed when the object is destroyed."""
        if self.conn:
            self.conn.close()
