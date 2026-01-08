import sqlite3
from datetime import datetime, timedelta
import logging
import time

class MessageDB:
    def __init__(self, db_path='messages.db', max_retries=3):
        self.db_path = db_path
        self.max_retries = max_retries
        self.conn = None
        self._connect()
        self._setup_database()
    
    def _connect(self):
        """Establish database connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self.conn.execute("PRAGMA journal_mode=WAL")
                logging.info(f"✅ Database connected: {self.db_path}")
                return
            except sqlite3.Error as e:
                logging.error(f"❌ Database connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                else:
                    raise
    
    def _ensure_connection(self):
        """Ensure database connection is alive"""
        try:
            self.conn.execute("SELECT 1")
        except (sqlite3.Error, AttributeError):
            logging.warning("⚠️ Database connection lost, reconnecting...")
            self._connect()
    
    def _setup_database(self):
        """Create table, migrate schema, then create indexes"""
        self._ensure_connection()
        cursor = self.conn.cursor()
        
        # Step 1: Create base table if not exists
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
        
        # Step 2: Migrate schema - add new columns if they don't exist
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN user_id INTEGER")
            logging.info("📦 Added user_id column")
        
        if 'username' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN username TEXT")
            logging.info("📦 Added username column")
        
        self.conn.commit()
        
        # Step 3: Create indexes (now columns exist)
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_timestamp 
            ON messages(chat_id, timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_username 
            ON messages(username)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_id 
            ON messages(user_id)
        ''')
        self.conn.commit()
        logging.info("✅ Database schema ready")
    
    def add_message(self, chat_id, user_id, user_name, username, message_text):
        """Save a message with full user info"""
        self._ensure_connection()
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO messages (chat_id, user_id, user_name, username, message_text)
                VALUES (?, ?, ?, ?, ?)
            ''', (chat_id, user_id, user_name, username, message_text))
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"❌ Failed to save message: {e}")
            self._connect()
    
    def get_messages_today(self, chat_id):
        self._ensure_connection()
        try:
            cursor = self.conn.cursor()
            today = datetime.now().date()
            cursor.execute('''
                SELECT user_name, message_text, timestamp, username
                FROM messages
                WHERE chat_id = ? AND DATE(timestamp) = ?
                ORDER BY timestamp
            ''', (chat_id, today))
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"❌ Failed to fetch messages: {e}")
            return []
    
    def get_messages_last_hours(self, chat_id, hours):
        self._ensure_connection()
        try:
            cursor = self.conn.cursor()
            time_ago = datetime.now() - timedelta(hours=hours)
            cursor.execute('''
                SELECT user_name, message_text, timestamp, username
                FROM messages
                WHERE chat_id = ? AND timestamp >= ?
                ORDER BY timestamp
            ''', (chat_id, time_ago))
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"❌ Failed to fetch messages: {e}")
            return []
    
    def get_messages_by_person(self, chat_id, person_names, hours=None):
        """Get messages from specific person(s) - searches by name OR username (case-insensitive)"""
        self._ensure_connection()
        try:
            cursor = self.conn.cursor()
            
            # Build conditions for each name (match user_name OR username)
            conditions = []
            params = [chat_id]
            
            for name in person_names:
                name_lower = name.lower()
                conditions.append("(LOWER(user_name) = ? OR LOWER(username) = ?)")
                params.extend([name_lower, name_lower])
            
            name_condition = " OR ".join(conditions)
            
            if hours:
                time_ago = datetime.now() - timedelta(hours=hours)
                query = f'''
                    SELECT user_name, message_text, timestamp, username
                    FROM messages
                    WHERE chat_id = ? AND ({name_condition}) AND timestamp >= ?
                    ORDER BY timestamp
                '''
                params.append(time_ago)
            else:
                today = datetime.now().date()
                query = f'''
                    SELECT user_name, message_text, timestamp, username
                    FROM messages
                    WHERE chat_id = ? AND ({name_condition}) AND DATE(timestamp) = ?
                    ORDER BY timestamp
                '''
                params.append(today)
            
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"❌ Failed to fetch messages by person: {e}")
            return []
    
    def get_participants(self, chat_id):
        """Get list of all participants who sent messages today with their usernames"""
        self._ensure_connection()
        try:
            cursor = self.conn.cursor()
            today = datetime.now().date()
            cursor.execute('''
                SELECT DISTINCT user_name, username
                FROM messages
                WHERE chat_id = ? AND DATE(timestamp) = ?
                ORDER BY user_name
            ''', (chat_id, today))
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"❌ Failed to fetch participants: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logging.info("📁 Database connection closed")
