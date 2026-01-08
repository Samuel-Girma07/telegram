from flask import Flask
from threading import Thread
import logging

# Hide Flask logs to keep console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')

@app.route('/')
def home():
    return "I am alive! Bot is running."

def run():
    # host='0.0.0.0' is CRITICAL for Render
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
