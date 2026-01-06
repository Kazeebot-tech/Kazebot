import os
import json
import random
import string
from datetime import datetime, timedelta

from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
import threading
import uvicorn

# =========================
# CONFIG (IKAW MAG EDIT)
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
KEY_PREFIX = "MOD"
KEY_DB = "keys.json"

# =========================
# UTILS
# =========================
def load_keys():
    with open(KEY_DB, "r") as f:
        return json.load(f)

def save_keys(data):
    with open(KEY_DB, "w") as f:
        json.dump(data, f, indent=4)

def generate_key():
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    return f"{KEY_PREFIX}-{rand}"

# =========================
# TELEGRAM BOT
# =========================
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

    days = int(context.args[0])
    key = generate_key()

    db = load_keys()
    db[key] = {
        "expire": (datetime.now() + timedelta(days=days)).isoformat(),
        "used": False
    }
    save_keys(db)

    await update.message.reply_text(
        f"✅ KEY GENERATED\n\n"
        f"🔑 {key}\n"
        f"⏳ {days} days"
    )

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

def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("listkeys", listkeys))
    app.run_polling()

# =========================
# API (FOR MOD MENU)
# =========================
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

def run_api():
    uvicorn.run(api, host="0.0.0.0", port=8000)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    threading.Thread(target=run_api).start()
    run_bot()
