import os
from flask import Flask, request
import requests
from threading import Lock

app = Flask(__name__)

# Load Telegram config from environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise Exception("Set BOT_TOKEN and CHAT_ID in environment variables!")

# In-memory ban list
ban_list = set()
lock = Lock()

# Send Telegram message
def notify_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": msg})

# Routes
@app.route("/check")
def check_device():
    device = request.args.get("device")
    if not device:
        return "MISSING", 400
    with lock:
        if device in ban_list:
            return "BANNED"
    return "OK"

@app.route("/ban")
def ban_device():
    device = request.args.get("device")
    if not device:
        return "MISSING", 400
    with lock:
        ban_list.add(device)
    notify_telegram(f"🚫 Device banned: {device}")
    return f"{device} BANNED!"

@app.route("/unban")
def unban_device():
    device = request.args.get("device")
    if not device:
        return "MISSING", 400
    with lock:
        ban_list.discard(device)
    notify_telegram(f"✅ Device unbanned: {device}")
    return f"{device} UNBANNED!"

@app.route("/")
def index():
    return "Server online!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
