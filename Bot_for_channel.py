import os
import re
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.constants import MessageEntityType
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime
import pytz
import time

app_web = Flask(__name__)

# OWNER_ID from Render environment variable
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

@app_web.route("/")
def home():
    return "Bot is online!"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app_web.run(host="0.0.0.0", port=port)).start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    full_name = user.full_name.strip() if user and user.full_name else "Player"

    start_message = (
        f"👋 Hi <b>{full_name}</b>, I am <b>Kazebot</b>! 🤖\n\n"
        "🎮 I will help moderate this channel.\n"
        "⚠️ Forwarded messages and <b>t.me</b> links are not allowed.\n\n"
        "Please <i>stay active and cooperative</i> while enjoying 🔥\n"
        "Type <code>/help</code> to see what I can do."
    )

    await update.message.reply_text(start_message, parse_mode="HTML")

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.message
    if not msg or not msg.new_chat_members:
        return

    for m in msg.new_chat_members:
        full = (m.full_name or m.first_name or "Player").strip()

        welcome_message = (
            f"👋 Hello <b>{full}</b>, welcome to <b>Palaro</b>! 🎮🔥\n\n"
            "📌 Please check the pinned rules before playing.\n"
            "💬 Stay active and follow announcements for updates.\n\n"
            "👉 If you haven't joined our main channel yet, join here:\n"
            "<a href='https://t.me/+wkXVYyqiRYplZjk1'>🌐 Main Channel</a>"
        )

        await chat.send_message(welcome_message, parse_mode="HTML", disable_web_page_preview=True)

# -------------------- Moderation Helpers --------------------
def msg_is_forwarded(msg) -> bool:
    return bool(
        getattr(msg, "forward_origin", None)
        or getattr(msg, "forward_date", None)
        or getattr(msg, "forward_from", None)
        or getattr(msg, "forward_from_chat", None)
        or getattr(msg, "forward_sender_name", None)
    )

def msg_has_link(msg) -> bool:
    text = (msg.text or msg.caption or "")[:4096]
    t = text.lower()

    if re.search(r"(https?://|www\.|t\.me/|telegram\.me/)", t):
        return True

    if re.search(r"\b[a-z0-9-]+\.(com|net|org|io|co|me|gg|app|xyz|site|dev|ph)\b", t):
        return True

    entities = (msg.entities or []) + (getattr(msg, "caption_entities", []) or [])
    for e in entities:
        if e.type in (MessageEntityType.URL, MessageEntityType.TEXT_LINK):
            return True

    return False

async def send_temp_warning(chat, text: str, seconds: int = 5):
    try:
        warn = await chat.send_message(text)
        await asyncio.sleep(seconds)
        await warn.delete()
    except:
        pass

async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user:
        return

    user_id = msg.from_user.id

    # Owner exception
    if OWNER_ID and user_id == OWNER_ID:
        return

    try:
        if msg_is_forwarded(msg):
            await msg.delete()
            await send_temp_warning(msg.chat, "⚠️ Forward messages are not allowed to prevent ads/spam.")
            return

        if msg_has_link(msg):
            await msg.delete()
            await send_temp_warning(msg.chat, "⚠️ Links are not allowed kupal!")
            return
    except Exception as e:
        print("moderate error:", e)

async def detect_pogi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.lower()

    if "kaze" in text:
        await msg.reply_text("Pogi si Kaze!")
        return

    if "kuri" in text:
        await msg.reply_text("Pogi")
        return
        
    if "phia" in text:
        await msg.reply_text("Phia maganda")
        return

    if re.search(r"\b(hi|hello|hey|hoy|yo)\b", text):
        await update.message.reply_text("👋 Hi! Kumusta ka?")
        return

    if re.search(r"\b(thanks|thank you|thx|salamat)\b", text):
        await update.message.reply_text("🙏 Walang anuman! 😊")
        return

    if re.search(r"\b(good night|gn|gabing gabi)\b", text):
        await update.message.reply_text("🌙 Good night too😴")
        return

    if re.search(r"\b(good morning|gm|umaga na)\b", text):
        await update.message.reply_text("☀️ Good morning too!😏")
        return

    if re.search(r"\b(anong oras naba?|time|what time is it?)\b", text):
        tz = pytz.timezone("Asia/Manila")
        now = datetime.now(tz)
        time_now = now.strftime("%I:%M %p")
        await update.message.reply_text(f"⏰ Time check: **{time_now}**", parse_mode="Markdown")
        return

    if re.search(r"\b(ano ang pangalan mo|who are you)\b", text):
        await msg.reply_text("🤖 Ako si Kazebot! Bot na tumutulong sa channel na ito.")
        return

    if re.search(r"\b(gg|good game)\b", text):
        await msg.reply_text("🎮 GG! Nice play!")
        return

    if re.search(r"\b(oops|oh no|uh oh)\b", text):
        await msg.reply_text("🤥 Ehh?")
        return

async def report_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not context.args:
        await msg.reply_text(
            "⚠️ Usage:\n/report @username reason\nExample: /report @user spamming links"
        )
        return

    reported_user = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
    chat = update.effective_chat

    reporter_name = update.effective_user.full_name or update.effective_user.username

    await msg.reply_text("✅ Your report has been sent to the admins Owner.")

    admins = await context.bot.get_chat_administrators(chat.id)

    for admin in admins:
        if admin.user.is_bot:
            continue
        try:
            await context.bot.send_message(
                admin.user.id,
                f"🚨 *Report Notification*\n\n"
                f"👤 Reported user: {reported_user}\n"
                f"📝 Reason: {reason}\n"
                f"🕵️ Reported by: {reporter_name}\n"
                f"📍 Group: {chat.title}",
                parse_mode="Markdown"
            )
        except:
            pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *KAZEBOT COMMANDS*\n\n"
        "👤 *Member Commands:*\n"
        "/start - Greet and info about the bot\n"
        "/report @username reason - Report a user anonymously to admins\n"
        "/help - Show this list\n\n"
        "🔇 *Moderation Rules:*\n"
        "• Forwarded messages are deleted\n"
        "• Links are deleted\n\n"
        "Stay active and follow the rules! 🔥"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# ===== MAIN FUNCTION (ONE ONLY!) =====
def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN env var.")

    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_user))
    app.add_handler(CommandHandler("help", help_command))

    # Welcome new members
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    
    # Pogi detector & auto replies
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_pogi))

    # Moderation (anti-forward & anti-link)
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.CAPTION | filters.FORWARDED) & ~filters.COMMAND,
        moderate
    ))

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    keep_alive()
    main()
