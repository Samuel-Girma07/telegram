import sqlite3
import datetime
from config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Create table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  message_text TEXT,
                  timestamp DATETIME,
                  group_id INTEGER)''')
    conn.commit()
    conn.close()

def save_message(user_id, username, text, group_id):
    conn = get_connection()
    c = conn.cursor()
    timestamp = datetime.datetime.now()
    c.execute("INSERT INTO messages (user_id, username, message_text, timestamp, group_id) VALUES (?, ?, ?, ?, ?)",
              (user_id, username, text, timestamp, group_id))
    conn.commit()
    conn.close()
    print(f"💾 Saved: {username}: {text[:20]}...")

def get_recent_messages(limit=50):
    conn = get_connection()
    c = conn.cursor()
    # Get last N messages
    c.execute("SELECT username, message_text FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    # Return reversed (chronological order)
    return rows[::-1]

def get_active_members():
    conn = get_connection()
    c = conn.cursor()
    # Get users active in last 24 hours
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    c.execute("SELECT DISTINCT username FROM messages WHERE timestamp > ?", (yesterday,))
    users = [row[0] for row in c.fetchall() if row[0]]
    conn.close()
    return users

def get_person_stats(username_query):
    conn = get_connection()
    c = conn.cursor()
    # Remove @ if present
    clean_name = username_query.replace("@", "")
    c.execute("SELECT COUNT(*) FROM messages WHERE username LIKE ?", (f"%{clean_name}%",))
    count = c.fetchone()[0]
    conn.close()
    return count
