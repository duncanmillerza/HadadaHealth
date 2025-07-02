import sqlite3

# Path to your existing bookings.db file
db_path = "data/bookings.db"

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create the treatment_notes table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS billing_modifiers (
        modifier_code TEXT,
        modifier_name TEXT,
        modifier_description TEXT,
        modifier_effect TEXT,
        modifier_multiplier NUMERIC,
        profession TEXT
    );
""")

# Commit and close the connection
conn.commit()
conn.close()

print("✅ modifier table created successfully.")