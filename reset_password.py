import sqlite3
import bcrypt

# 1) Pick your username and the new password you want
USERNAME = "admin"           # ← change to your user’s username
NEW_PASSWORD = "admin123"  # ← change to whatever you like

# 2) Hash it
hashed = bcrypt.hashpw(NEW_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# 3) Update the DB
conn = sqlite3.connect("data/bookings.db")
conn.execute(
    "UPDATE users SET password_hash = ? WHERE username = ?",
    (hashed, USERNAME)
)
conn.commit()
conn.close()

print(f"Password for '{USERNAME}' has been reset to '{NEW_PASSWORD}'.")