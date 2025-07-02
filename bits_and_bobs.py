import sqlite3

conn = sqlite3.connect("data/bookings.db")
cursor = conn.cursor()

# Add the patient_id column if it doesn't exist
try:
    cursor.execute("ALTER TABLE bookings ADD COLUMN patient_id INTEGER")
    print("✅ 'patient_id' column added.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ️ 'patient_id' column already exists.")
    else:
        raise

conn.commit()
conn.close()