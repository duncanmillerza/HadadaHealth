import sqlite3

def init_billing_tables():
    with sqlite3.connect("data/bookings.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS billing_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                description TEXT,
                base_fee REAL NOT NULL,
                profession TEXT NOT NULL
            );
        """)
        print("✅ billing_codes table created or already exists.")

init_billing_tables()