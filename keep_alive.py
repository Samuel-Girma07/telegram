from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "✅ Telegram Summarizer Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
