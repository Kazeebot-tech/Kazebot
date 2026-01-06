import os
import json
import random
import string
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Application
import uvicorn

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
KEY_PREFIX = "MOD"
KEY_DB = "keys.json"

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"  # Secure path with token
WEBHOOK_URL = f"https://kazebot-kybb.onrender.com{WEBHOOK_PATH}"  # Palitan mo yung your-service-name

# =========================
# UTILS (same as yours)
# =========================
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

# =========================
# TELEGRAM BOT HANDLERS (same)
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
    # ... (same as your code)

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (same)

async def listkeys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (same)

# =========================
# FASTAPI APP
# =========================
api = FastAPI()

# Your existing /check endpoint
@api.get("/check")
def check_key(key: str):
    # ... (same as your code)

# Webhook handler for Telegram updates
@api.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request, application: Application):
    """Handle incoming Telegram updates"""
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"ok": True}

# Optional: Health check endpoint para sure sa Render
@api.get("/")
async def health():
    return {"status": "ok"}

# =========================
# MAIN
# =========================
async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("revoke", revoke))
    application.add_handler(CommandHandler("listkeys", listkeys))

    # Inject application to FastAPI routes (dependency-like)
    api.state.application = application

    # Set webhook once on startup
    await application.bot.set_webhook(url=WEBHOOK_URL)

    # Run FastAPI with Uvicorn
    config = uvicorn.Config(api, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
