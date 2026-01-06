import os
import json
import random
import string
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

import uvicorn

# ================= CONFIG =================
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

KEY_DB = "keys.json"
KEY_PREFIX = "LGL"

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://kazebot-kybb.onrender.com{WEBHOOK_PATH}"

# ================= UTILS =================
def load_keys():
    if not os.path.exists(KEY_DB):
        return {}
    with open(KEY_DB, "r") as f:
        return json.load(f)

def save_keys(data):
    with open(KEY_DB, "w") as f:
        json.dump(data, f, indent=4)

def generate_key():
    return f"{KEY_PREFIX}-" + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=16)
    )

# ================= BOT COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
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

    data = load_keys()
    data[key] = {"expire": expire, "revoked": False}
    save_keys(data)

    await update.message.reply_text(f"✅ KEY:\n{key}\n⏳ {days} days")

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    key = context.args[0]
    data = load_keys()

    if key not in data:
        await update.message.reply_text("Key not found")
        return

    data[key]["revoked"] = True
    save_keys(data)
    await update.message.reply_text("🚫 Revoked")

async def listkeys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    data = load_keys()
    if not data:
        await update.message.reply_text("No keys.")
        return

    msg = ""
    for k, v in data.items():
        msg += f"{k}\nExp: {v['expire']}\nRevoked: {v['revoked']}\n\n"

    await update.message.reply_text(msg)

# ================= FASTAPI =================
api = FastAPI()

@api.get("/check")
def check_key(key: str):
    data = load_keys()

    if key not in data:
        return {"status": "invalid"}

    k = data[key]
    if k["revoked"]:
        return {"status": "revoked"}

    if datetime.utcnow() > datetime.fromisoformat(k["expire"]):
        return {"status": "expired"}

    return {"status": "valid"}

@api.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    app: Application = api.state.bot
    update = Update.de_json(await request.json(), app.bot)
    await app.process_update(update)
    return {"ok": True}

@api.get("/")
def health():
    return {"status": "ok"}

# ================= MAIN =================
async def main():
    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("genkey", genkey))
    bot.add_handler(CommandHandler("revoke", revoke))
    bot.add_handler(CommandHandler("listkeys", listkeys))

    api.state.bot = bot
    await bot.bot.set_webhook(WEBHOOK_URL)

    uvicorn.run(api, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
