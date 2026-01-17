from flask import Flask, request
import requests
from threading import Lock

app = Flask(__name__)

# In-memory ban list
ban_list = set()
lock = Lock()

# Telegram bot settings
BOT_TOKEN = "8565522240:AAGXobXeoX2PVL2BH7VJvtnipr93A2XcjlI"
CHAT_ID = "7201369115"

# Send Telegram message function
def notify_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": msg})

# Check device
@app.route("/check")
def check_device():
    device = request.args.get("device")
    if not device:
        return "MISSING", 400
    with lock:
        if device in ban_list:
            return "BANNED"
    return "OK"

# Ban device
@app.route("/ban")
def ban_device():
    device = request.args.get("device")
    if not device:
        return "MISSING", 400
    with lock:
        ban_list.add(device)
    notify_telegram(f"🚫 Device banned: {device}")
    return f"{device} BANNED!"

# Unban device
@app.route("/unban")
def unban_device():
    device = request.args.get("device")
    if not device:
        return "MISSING", 400
    with lock:
        ban_list.discard(device)
    notify_telegram(f"✅ Device unbanned: {device}")
    return f"{device} UNBANNED!"

# Test server
@app.route("/")
def index():
    return "Render server online!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
