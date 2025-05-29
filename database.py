import sqlite3

DB_FILE = "radios.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                contact TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS radios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                radio_id TEXT,
                serial TEXT NOT NULL,
                model TEXT,
                assigned_to TEXT,
                notes TEXT,
                department_id TEXT,
                date_received TEXT,
                date_issued TEXT,
                date_returned TEXT,
                last_updated TEXT,
                status TEXT DEFAULT 'Active',
                missing TEXT DEFAULT 'No',
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS radio_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                radio_id INTEGER,
                change_type TEXT,
                field_changed TEXT,
                old_value TEXT,
                new_value TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                radio_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                date_service TEXT,
                lrc_service_num TEXT,
                date_sent TEXT,
                date_repaired TEXT,
                amount REAL,
                problem TEXT,
                notes TEXT,
                FOREIGN KEY (radio_id) REFERENCES radios(id) ON DELETE CASCADE
            )
        """)

        conn.commit()

def log_radio_change(cursor, radio_id, change_type, field_changed, old_value, new_value):
    cursor.execute("""
        INSERT INTO radio_changes (radio_id, change_type, field_changed, old_value, new_value)
        VALUES (?, ?, ?, ?, ?)
    """, (radio_id, change_type, field_changed, old_value, new_value))
