import os
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DATABASE = os.path.join(BASE_DIR, "products.db")

if DATABASE_URL:
    import psycopg2
    from psycopg2.extras import DictCursor
    IntegrityError = psycopg2.IntegrityError
else:
    IntegrityError = sqlite3.IntegrityError


class CursorWrapper:
    """Small compatibility layer so app.py can keep using ? placeholders."""

    def __init__(self, cursor, postgres=False):
        self._cursor = cursor
        self.postgres = postgres

    def execute(self, sql, params=None):
        if self.postgres:
            sql = sql.replace("?", "%s")
        if params is None:
            return self._cursor.execute(sql)
        return self._cursor.execute(sql, params)

    def executemany(self, sql, seq_of_params):
        if self.postgres:
            sql = sql.replace("?", "%s")
        return self._cursor.executemany(sql, seq_of_params)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class ConnectionWrapper:
    def __init__(self, connection, postgres=False):
        self._connection = connection
        self.postgres = postgres

    def cursor(self):
        return CursorWrapper(self._connection.cursor(), self.postgres)

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


def get_connection():
    if DATABASE_URL:
        connection = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=DictCursor
        )
        return ConnectionWrapper(connection, postgres=True)

    connection = sqlite3.connect(
        SQLITE_DATABASE,
        timeout=10
    )
    connection.row_factory = sqlite3.Row
    return ConnectionWrapper(connection, postgres=False)


def create_database():
    connection = get_connection()
    cursor = connection.cursor()

    if DATABASE_URL:
        # PostgreSQL schema used on Render.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                product_id TEXT UNIQUE NOT NULL,
                product_name TEXT NOT NULL,
                manufacturer TEXT NOT NULL,
                batch_number TEXT,
                manufacturing_date TEXT,
                expiry_date TEXT,
                price DOUBLE PRECISION,
                barcode TEXT,
                blockchain_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_history (
                id SERIAL PRIMARY KEY,
                product_id TEXT,
                customer_email TEXT,
                verification_status TEXT,
                verification_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id SERIAL PRIMARY KEY,
                product_id TEXT,
                customer_email TEXT,
                complaint TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        # Permanent blockchain storage in PostgreSQL.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blockchain_blocks (
                id SERIAL PRIMARY KEY,
                block_index INTEGER UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                hash TEXT UNIQUE NOT NULL
            )
        """)

    else:
        # SQLite schema for local VS Code development.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT UNIQUE NOT NULL,
                product_name TEXT NOT NULL,
                manufacturer TEXT NOT NULL,
                batch_number TEXT,
                manufacturing_date TEXT,
                expiry_date TEXT,
                price REAL,
                barcode TEXT,
                blockchain_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT,
                customer_email TEXT,
                verification_status TEXT,
                verification_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT,
                customer_email TEXT,
                complaint TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blockchain_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_index INTEGER UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                hash TEXT UNIQUE NOT NULL
            )
        """)

    cursor.execute("""
        SELECT * FROM users WHERE email = ?
    """, ("admin@gmail.com",))

    admin = cursor.fetchone()

    if admin is None:
        cursor.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "Administrator",
            "admin@gmail.com",
            "admin123",
            "admin"
        ))

    connection.commit()
    connection.close()
