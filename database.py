import sqlite3

conn = sqlite3.connect("patients.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    phone TEXT PRIMARY KEY,
    created_at TEXT,
    first_contact_time TEXT,
    review_sent INTEGER DEFAULT 0,
    reminder_sent INTEGER DEFAULT 0
)
""")

conn.commit()
conn.close()

print("Database created")