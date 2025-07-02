import sqlite3

def list_professions_from_billing():
    db_path = "data/bookings.db"  # adjust path if needed
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT DISTINCT profession FROM billing_codes;")
        professions = [row[0] for row in cursor.fetchall()]
    
    print("✅ Professions found in billing_codes table:")
    for prof in professions:
        print("-", prof)

if __name__ == "__main__":
    list_professions_from_billing()