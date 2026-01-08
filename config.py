import os

# Load token from Render environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found! Add it in Render Environment Variables.")

DB_NAME = "chat_history.db"
