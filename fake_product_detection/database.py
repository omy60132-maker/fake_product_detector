import sqlite3

DATABASE = "products.db"


def get_connection():
    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    return connection


def create_database():

    connection = get_connection()
    cursor = connection.cursor()

    # =========================
    # USERS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL
        )
    """)

    # =========================
    # PRODUCTS
    # =========================

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

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # VERIFICATION HISTORY
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_id TEXT,

            customer_email TEXT,

            verification_status TEXT,

            verification_time TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # COMPLAINTS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_id TEXT,

            customer_email TEXT,

            complaint TEXT,

            status TEXT DEFAULT 'Pending',

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP
        )
    """)

    # =========================
    # DEFAULT ADMIN
    # =========================

    cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (
        "admin@gmail.com",
    ))

    admin = cursor.fetchone()

    if admin is None:

        cursor.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role
            )

            VALUES (?, ?, ?, ?)
        """, (

            "Administrator",

            "admin@gmail.com",

            "admin123",

            "admin"
        ))

    connection.commit()

    connection.close()