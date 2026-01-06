import os
import json
import random
import string
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

KEY_PREFIX = "MOD"
KEY_DB = "keys.json"

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://kazebot-kybb.onrender.com{WEBHOOK_PATH}"

# =========================
# FASTAPI
# =========================
api = FastAPI()
application = None

# =========================
# UTILS
# =========================
def load_keys():
    if not os.path.exists(KEY_DB):
        return {}
    with open(KEY_DB, "r") as f:
        return json.load(f)

def save_keys(data):
    with open(KEY_DB, "w") as f:
        json.dump(data, f, indent=4)

def generate_key():
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    return f"{KEY_PREFIX}-{rand}"

# =========================
# TELEGRAM COMMANDS
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
    expires = (datetime.utcnow() + timedelta(days=days)).isoformat()

    data = load_keys()
    data[key] = {
        "expires": expires,
        "active": True
    }
    save_keys(data)

    await update.message.reply_text(
        f"✅ KEY GENERATED\n\n"
        f"🔑 {key}\n"
        f"⏰ Expires in {days} days"
    )

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /revoke <key>")
        return

    key = context.args[0]
    data = load_keys()

    if key not in data:
        await update.message.reply_text("❌ Key not found")
        return

    data[key]["active"] = False
    save_keys(data)

    await update.message.reply_text(f"🚫 Key revoked:\n{key}")

async def listkeys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    data = load_keys()
    if not data:
        await update.message.reply_text("No keys found.")
        return

    msg = "🔑 ACTIVE KEYS:\n\n"
    for k, v in data.items():
        status = "✅" if v["active"] else "❌"
        msg += f"{status} {k}\n⏰ {v['expires']}\n\n"

    await update.message.reply_text(msg)

# =========================
# API ENDPOINT (FOR LGL)
# =========================
@api.get("/check")
def check_key(key: str):
    data = load_keys()

    if key not in data:
        return {"status": "invalid"}

    info = data[key]
    if not info["active"]:
        return {"status": "revoked"}

    if datetime.utcnow() > datetime.fromisoformat(info["expires"]):
        return {"status": "expired"}

    return {
        "status": "valid",
        "expires": info["expires"]
    }

# =========================
# TELEGRAM WEBHOOK
# =========================
@api.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"ok": True}

# =========================
# STARTUP
# =========================
@api.on_event("startup")
async def startup():
    global application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("revoke", revoke))
    application.add_handler(CommandHandler("listkeys", listkeys))

    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)

# =========================
# HEALTH
# =========================
@api.get("/")
def root():
    return {"status": "ok"}
