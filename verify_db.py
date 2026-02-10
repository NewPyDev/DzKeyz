import sqlite3
import os

# Ensure the database exists
if not os.path.exists('store.db'):
    print("Database file 'store.db' not found.")
    exit(1)

conn = sqlite3.connect('store.db')
cursor = conn.cursor()

# Check if reviews table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'")
table = cursor.fetchone()

if table:
    print("✅ Table 'reviews' exists.")

    # Check columns
    cursor.execute("PRAGMA table_info(reviews)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
else:
    print("❌ Table 'reviews' does not exist.")

conn.close()
