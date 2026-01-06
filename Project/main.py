import os
from threading import Thread
from flask import Flask
import json
import random
import string
from datetime import datetime, timedelta
import asyncio

from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import uvicorn

# ===== WEBKEEP ALIVE =====
app_web = Flask(__name__)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

@app_web.route("/")
def home():
    return "Bot is online!"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app_web.run(host="0.0.0.0", port=port)).start()
    
# CONFIG
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
KEY_PREFIX = "MOD"
KEY_DB = "keys.json"

# UTILS
def load_keys():
    try:
        with open(KEY_DB, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_keys(data):
    with open(KEY_DB, "w") as f:
        json.dump(data, f, indent=4)

def generate_key():
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    return f"{KEY_PREFIX}-{rand}"

# TELEGRAM BOT HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "🔐 Key Panel Bot\n\n"
        "/genkey <days>\n"
        "/revoke <key>\n"
        "/listkeys"
    )

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /genkey <days>")
        return

    try:
        days = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid number")
        return

    key = generate_key()
    db = load_keys()
    db[key] = {
        "expire": (datetime.now() + timedelta(days=days)).isoformat(),
        "used": False
    }
    save_keys(db)

    await update.message.reply_text(f"✅ KEY GENERATED\n\n🔑 {key}\n⏳ {days} days")

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /revoke <key>")
        return

    key = context.args[0]
    db = load_keys()
    if key not in db:
        await update.message.reply_text("❌ Key not found")
        return

    del db[key]
    save_keys(db)
    await update.message.reply_text("🗑️ Key revoked")

async def listkeys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    db = load_keys()
    if not db:
        await update.message.reply_text("No keys.")
        return

    msg = "🔑 ACTIVE KEYS:\n\n"
    for k, v in db.items():
        msg += f"{k}\nExpire: {v['expire']}\n\n"

    await update.message.reply_text(msg)

# API FOR MOD MENU
api = FastAPI()

@api.get("/check")
def check_key(key: str):
    db = load_keys()
    if key not in db:
        return {"status": "INVALID"}

    info = db[key]
    if datetime.fromisoformat(info["expire"]) < datetime.now():
        return {"status": "EXPIRED"}

    return {"status": "VALID"}

# MAIN ASYNC ENTRY
async def main():
    # Start bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("listkeys", listkeys))

    # Run bot and API concurrently
    api_port = int(os.environ.get("PORT", 8000))
    api_task = uvicorn.Server(
        uvicorn.Config(api, host="0.0.0.0", port=api_port, log_level="info")
    )

    await asyncio.gather(
        app.run_polling(),
        api_task.serve()
    )

if __name__ == "__main__":
    keep_alive()
    main()
