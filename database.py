import sqlite3
import datetime

# Name of the database file
DB_NAME = "chat_logs.db"

def get_connection():
    """Create a fresh connection for every single request to prevent data mixing."""
    conn = sqlite3.connect(DB_NAME)
    # This allows us to access columns by name (row['message'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database table."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER,
            username TEXT,
            message_text TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def save_message(chat_id, user_id, username, text):
    """Save a message securely."""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.now()
    
    c.execute('''
        INSERT INTO messages (chat_id, user_id, username, message_text, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (chat_id, user_id, username, text, now))
    
    conn.commit()
    conn.close()

def get_messages(chat_id, limit=100):
    """
    Get messages ONLY for the specific chat_id.
    Returns them in chronological order (Oldest -> Newest).
    """
    conn = get_connection()
    c = conn.cursor()
    
    # STRICT filtering by chat_id ensures groups never mix
    c.execute('''
        SELECT username, message_text 
        FROM messages 
        WHERE chat_id = ? 
        ORDER BY id DESC 
        LIMIT ?
    ''', (chat_id, limit))
    
    rows = c.fetchall()
    conn.close()
    
    # Reverse to get chronological order (Oldest first)
    return rows[::-1]

def get_active_users(chat_id):
    """Get distinct users from the last 24 hours for a specific group."""
    conn = get_connection()
    c = conn.cursor()
    
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    
    c.execute('''
        SELECT DISTINCT username 
        FROM messages 
        WHERE chat_id = ? AND timestamp > ?
    ''', (chat_id, yesterday))
    
    users = [row['username'] for row in c.fetchall() if row['username']]
    conn.close()
    return users

def get_person_stats(chat_id, target_name):
    """Count messages for a specific person in a specific group."""
    conn = get_connection()
    c = conn.cursor()
    
    # Remove @ if typed by user
    clean_name = target_name.replace("@", "")
    
    c.execute('''
        SELECT COUNT(*) 
        FROM messages 
        WHERE chat_id = ? AND username LIKE ?
    ''', (chat_id, f"%{clean_name}%"))
    
    count = c.fetchone()[0]
    conn.close()
    return count
