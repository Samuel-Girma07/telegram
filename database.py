import sqlite3
from datetime import datetime, timedelta

class MessageDB:
    def __init__(self):
        self.conn = sqlite3.connect('messages.db', check_same_thread=False)
        self.create_table()
    
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_name TEXT,
                message_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def add_message(self, chat_id, user_name, message_text):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO messages (chat_id, user_name, message_text)
            VALUES (?, ?, ?)
        ''', (chat_id, user_name, message_text))
        self.conn.commit()
    
    def get_messages_today(self, chat_id):
        cursor = self.conn.cursor()
        today = datetime.now().date()
        cursor.execute('''
            SELECT user_name, message_text, timestamp
            FROM messages
            WHERE chat_id = ? AND DATE(timestamp) = ?
            ORDER BY timestamp
        ''', (chat_id, today))
        return cursor.fetchall()
    
    def get_messages_last_hours(self, chat_id, hours):
        cursor = self.conn.cursor()
        time_ago = datetime.now() - timedelta(hours=hours)
        cursor.execute('''
            SELECT user_name, message_text, timestamp
            FROM messages
            WHERE chat_id = ? AND timestamp >= ?
            ORDER BY timestamp
        ''', (chat_id, time_ago))
        return cursor.fetchall()
    
    def get_messages_by_person(self, chat_id, person_names, hours=None):
        """Get messages from specific person(s)"""
        cursor = self.conn.cursor()
        
        placeholders = ','.join('?' * len(person_names))
        
        if hours:
            time_ago = datetime.now() - timedelta(hours=hours)
            query = f'''
                SELECT user_name, message_text, timestamp
                FROM messages
                WHERE chat_id = ? AND user_name IN ({placeholders}) AND timestamp >= ?
                ORDER BY timestamp
            '''
            params = [chat_id] + person_names + [time_ago]
        else:
            today = datetime.now().date()
            query = f'''
                SELECT user_name, message_text, timestamp
                FROM messages
                WHERE chat_id = ? AND user_name IN ({placeholders}) AND DATE(timestamp) = ?
                ORDER BY timestamp
            '''
            params = [chat_id] + person_names + [today]
        
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def get_participants(self, chat_id):
        """Get list of all participants who sent messages today"""
        cursor = self.conn.cursor()
        today = datetime.now().date()
        cursor.execute('''
            SELECT DISTINCT user_name
            FROM messages
            WHERE chat_id = ? AND DATE(timestamp) = ?
            ORDER BY user_name
        ''', (chat_id, today))
        return [row[0] for row in cursor.fetchall()]
