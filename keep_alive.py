from flask import Flask, jsonify
from threading import Thread
from datetime import datetime
import logging

# Suppress Flask's default logging to reduce noise
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

app = Flask('')

# Track bot status
bot_status = {
    "started_at": datetime.now().isoformat(),
    "is_running": True,
    "last_ping": None
}

@app.route('/')
def home():
    """Main endpoint - UptimeRobot should ping this"""
    bot_status["last_ping"] = datetime.now().isoformat()
    return "✅ Telegram Summarizer Bot is running!"

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    bot_status["last_ping"] = datetime.now().isoformat()
    return jsonify({
        "status": "healthy",
        "bot_running": bot_status["is_running"],
        "started_at": bot_status["started_at"],
        "last_ping": bot_status["last_ping"]
    }), 200

@app.route('/ping')
def ping():
    """Simple ping endpoint for UptimeRobot"""
    bot_status["last_ping"] = datetime.now().isoformat()
    return "pong", 200

def run():
    """Run Flask server"""
    try:
        app.run(host='0.0.0.0', port=8080, threaded=True)
    except Exception as e:
        logging.error(f"❌ Flask server error: {e}")

def keep_alive():
    """Start Flask server in a daemon thread"""
    t = Thread(target=run, daemon=True)
    t.start()
    logging.info("🌐 Keep-alive server started on port 8080")
    return t

def set_bot_status(running: bool):
    """Update bot status for health checks"""
    bot_status["is_running"] = running
