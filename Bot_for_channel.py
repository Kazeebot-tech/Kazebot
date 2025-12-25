import os
import asyncio
from flask import Flask
from telegram import Update, MessageEntity
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ===== CONFIG =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
PORT = int(os.getenv("PORT", 10000))

if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")

# ===== FLASK =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Kazebot is running!"

# ===== HELPERS =====
def msg_is_forwarded(msg):
    return bool(
        msg.forward_origin
        or msg.forward_from
        or msg.forward_from_chat
        or msg.forward_sender_name
    )

def msg_has_tme_link(msg):
    text = (msg.text or msg.caption or "").lower()
    if "t.me/" in text or "telegram.me/" in text:
        return True

    entities = (msg.entities or []) + (msg.caption_entities or [])
    for e in entities:
        if e.type in (MessageEntity.URL, MessageEntity.TEXT_LINK):
            url = (e.url or "").lower()
            if "t.me/" in url or "telegram.me/" in url:
                return True
    return False

async def temp_warn(chat, text, sec=5):
    msg = await chat.send_message(text)
    await asyncio.sleep(sec)
    try:
        await msg.delete()
    except:
        pass

# ===== MODERATION =====
async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    user_id = msg.from_user.id

    if OWNER_ID and user_id == OWNER_ID:
        return

    try:
        member = await context.bot.get_chat_member(msg.chat.id, user_id)
        if member.status in ("administrator", "creator"):
            return
    except:
        pass

    if msg_is_forwarded(msg):
        await msg.delete()
        await temp_warn(msg.chat, "⚠️ Forwarded messages are not allowed.")
        return

    if msg_has_tme_link(msg):
        await msg.delete()
        await temp_warn(msg.chat, "⚠️ t.me links are not allowed.")
        return

# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.full_name if user else "Player"
    await update.message.reply_text(
        f"👋 Hi {name}!\n\n"
        "I'm Kazebot 🤖\n"
        "No forwarded messages\n"
        "No t.me links\n\n"
        "Type /help"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Start bot\n"
        "/help - Commands\n"
        "/report @user reason - Report member\n\n"
        "Rules:\n"
        "- No forwarded messages\n"
        "- No t.me links"
    )

# ===== MAIN ASYNC =====
async def main():
    tg_app = Application.builder().token(TOKEN).build()

    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("help", help_cmd))
    tg_app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.CAPTION | filters.FORWARDED) & ~filters.COMMAND,
            moderate,
        )
    )

    await tg_app.initialize()
    await tg_app.start()
    await tg_app.bot.initialize()

    # Flask runs forever
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    asyncio.run(main())
