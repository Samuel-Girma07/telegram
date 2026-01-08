from flask import Flask
from threading import Thread

# Create the Flask application
app = Flask('')

@app.route('/')
def home():
    # This simple message tells UptimeRobot the bot is online
    return "I am alive! Bot is running."

def run():
    # CRITICAL FIX: host='0.0.0.0' is required for Render to access the server.
    # If this is set to '127.0.0.1', UptimeRobot will always show "Down".
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # Runs the web server in a separate thread so it doesn't block the bot
    t = Thread(target=run)
    t.start()
