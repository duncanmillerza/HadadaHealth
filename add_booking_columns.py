import sqlite3

def add_columns(db_path="data/bookings.db"):
    """
    Connects to the SQLite database at `db_path` and adds two columns to the `bookings` table:
    - note_completed: INTEGER (0 or 1), default 0
    - billing_completed: INTEGER (0 or 1), default 0
    If the columns already exist, they are left unchanged.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add note_completed column
    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN note_completed INTEGER DEFAULT 0;")
        print("Added column 'note_completed'")
    except sqlite3.OperationalError:
        print("Column 'note_completed' already exists, skipping.")

    # Add billing_completed column
    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN billing_completed INTEGER DEFAULT 0;")
        print("Added column 'billing_completed'")
    except sqlite3.OperationalError:
        print("Column 'billing_completed' already exists, skipping.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns()
