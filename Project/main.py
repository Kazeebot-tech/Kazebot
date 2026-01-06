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

import uvicorn

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

KEY_PREFIX = "LGL"
KEY_DB = "keys.json"

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://kazebot-kybb.onrender.com{WEBHOOK_PATH}"

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
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    return f"{KEY_PREFIX}-{rand}"

# =========================
# TELEGRAM BOT COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "🔐 LGL KEY BOT\n\n"
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
    expire = (datetime.utcnow() + timedelta(days=days)).isoformat()

    keys = load_keys()
    keys[key] = {
        "expire": expire,
        "revoked": False
    }
    save_keys(keys)

    await update.message.reply_text(
        f"✅ KEY GENERATED\n\n"
        f"🔑 `{key}`\n"
        f"⏳ {days} days",
        parse_mode="Markdown"
    )

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /revoke <key>")
        return

    key = context.args[0]
    keys = load_keys()

    if key not in keys:
        await update.message.reply_text("❌ Key not found")
        return

    keys[key]["revoked"] = True
    save_keys(keys)

    await update.message.reply_text("🚫 Key revoked")

async def listkeys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keys = load_keys()
    if not keys:
        await update.message.reply_text("No keys found.")
        return

    msg = "📋 ACTIVE KEYS\n\n"
    for k, v in keys.items():
        status = "❌ REVOKED" if v["revoked"] else "✅ ACTIVE"
        msg += f"{k}\n{status}\nExp: {v['expire']}\n\n"

    await update.message.reply_text(msg)

# =========================
# FASTAPI
# =========================
api = FastAPI()

@api.get("/check")
def check_key(key: str):
    keys = load_keys()

    if key not in keys:
        return {"status": "invalid"}

    data = keys[key]

    if data["revoked"]:
        return {"status": "revoked"}

    if datetime.utcnow() > datetime.fromisoformat(data["expire"]):
        return {"status": "expired"}

    return {"status": "valid"}

@api.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    app = api.state.application
    update = Update.de_json(await request.json(), app.bot)
    await app.process_update(update)
    return {"ok": True}

@api.get("/")
def health():
    return {"status": "ok"}

# =========================
# MAIN
# =========================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("listkeys", listkeys))

    api.state.application = app
    await app.bot.set_webhook(WEBHOOK_URL)

    config = uvicorn.Config(api, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
