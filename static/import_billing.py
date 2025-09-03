import sqlite3
import csv
import os

csv_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "modifier_table.csv"))

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/bookings.db"))

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()

    with open(csv_file, newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                modifier_code = row["modifier_code"].strip()
                modifier_name = row["modifier_name"].strip()
                modifier_description = row["modifier_description"].strip()
                modifier_effect = row["modifier_effect"].strip()
                modifier_multiplier = float(row["modifier_multiplier"].strip()) if row["modifier_multiplier"].strip() else 1.0
                profession = row["profession"].strip()
            except KeyError as e:
                print(f"❌ Missing column in CSV: {e}")
                continue

            cursor.execute("""
                INSERT INTO billing_modifiers (modifier_code, modifier_name, modifier_description, modifier_effect, modifier_multiplier, profession)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (modifier_code, modifier_name, modifier_description, modifier_effect, modifier_multiplier, profession))
    conn.commit()

print("✅ Billing codes imported from single CSV.")