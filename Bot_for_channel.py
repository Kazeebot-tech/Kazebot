import os
import re
import asyncio
from threading import Thread
from flask import Flask
from datetime import datetime
import pytz
from telegram import Update, MessageEntity
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ===== WEBKEEP ALIVE =====
app_web = Flask(__name__)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

@app_web.route("/")
def home():
    return "Bot is online!"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app_web.run(host="0.0.0.0", port=port)).start()

# ===== MODERATION HELPERS =====
def msg_is_forwarded(msg) -> bool:
    return bool(
        getattr(msg, "forward_origin", None)
        or getattr(msg, "forward_date", None)
        or getattr(msg, "forward_from", None)
        or getattr(msg, "forward_from_chat", None)
        or getattr(msg, "forward_sender_name", None)
    )

def msg_has_tme_link(msg) -> bool:
    text = (msg.text or msg.caption or "")[:4096]
    t = text.lower()

    # Block only t.me or telegram.me links in text
    if "t.me/" in t or "telegram.me/" in t:
        return True

    # Check clickable links (entities)
    entities = (msg.entities or []) + (msg.caption_entities or [])
    for e in entities:
        if e.type in (MessageEntity.URL, MessageEntity.TEXT_LINK):
            url = getattr(e, "url", "") or ""
            if "t.me/" in url.lower() or "telegram.me/" in url.lower():
                return True
    return False

async def send_temp_warning(chat, text: str, seconds: int = 5):
    warn = await chat.send_message(text)
    await asyncio.sleep(seconds)
    try:
        await warn.delete()
    except Exception:
        pass

# ===== MODERATION FUNCTION =====
async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user:
        return

    user_id = msg.from_user.id

    # OWNER exception
    if OWNER_ID and user_id == OWNER_ID:
        return

    # ADMIN / CREATOR exception
    try:
        member = await context.bot.get_chat_member(msg.chat.id, user_id)
        if member.status in ("administrator", "creator"):
            return
    except Exception:
        pass

    try:
        # DELETE forwarded messages
        if msg_is_forwarded(msg):
            await msg.delete()
            await send_temp_warning(msg.chat, "⚠️ Forward messages are not allowed!")
            return

        # DELETE t.me links
        if msg_has_tme_link(msg):
            await msg.delete()
            await send_temp_warning(msg.chat, "⚠️ t.me links are not allowed!")
            return

    except Exception as e:
        print("moderate error:", e)

# ===== START COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    full_name = user.full_name.strip() if user and user.full_name else "Player"

    start_message = (
        f"👋 Hi {full_name}! Welcome to Palaro 🎮🔥\n\n"
        "🤖 I'm here to help keep the channel clean and enjoyable.\n\n"
        "⚠️ Channel Rules:\n"
        "• No forwarded messages\n"
        "• No t.me links\n\n"
        "💬 Please stay active and respectful.\n"
        "🛠️ Type /help to see what I can do.\n\n"
        "🔥 Enjoy the game and have fun!"
    )

    await update.message.reply_text(start_message)
    
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.message
    if not msg or not msg.new_chat_members:
        return

    for m in msg.new_chat_members:
        full = (m.full_name or m.first_name or "Player").strip()

        welcome_message = (
            f"👋 Hello {full}, welcome to Palaro! 🎮🔥\n\n"
            "📌 Please check the pinned rules before playing.\n"
            "💬 Stay active and follow announcements for updates.\n\n"
            "👉 If you haven't joined our main channel yet, join here:\n"
            "https://t.me/+wkXVYyqiRYplZjk1"
        )

        await chat.send_message(welcome_message, disable_web_page_preview=True)
# ===== /HELP COMMAND =====
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 <b>Kazebot Commands</b>\n\n"
        "👤 <b>Member Commands:</b>\n"
        "/start - Greet and info about the bot\n"
        "/help - Show this help message"
        "/report @username reason - Report a user to admin and owner directly\n\n"
        "- Forwarded messages are not allowed\n"
        "- telegram links are not allowed\n\n"
        "Please follow the rules and have fun! 🔥"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

async def detect_pogi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.lower()

    if re.search(r"\bkaze\b", text):
        await msg.reply_text("Pogi si Kaze!")
        return

    if re.search(r"\bkuri\b", text):
        await msg.reply_text("Pogi")
        return
        
    if re.search(r"\bphia\b", text):
        await msg.reply_text("Phia maganda")
        return

    # ===== HI / HELLO =====
    if re.search(r"\b(hi|hello|hey|hoy|yo)\b", text):
        await update.message.reply_text("👋 Hi! Kumusta ka?")
        return

    # ===== THANK YOU =====
    if re.search(r"\b(thanks|thank you|thx|salamat)\b", text):
        await update.message.reply_text("🙏 Walang anuman! 😊")
        return

    # ===== GOOD NIGHT =====
    if re.search(r"\b(good night|gn|gabing gabi)\b", text):
        await update.message.reply_text("🌙 Good night too😴")
        return

    # ===== GOOD MORNING =====
    if re.search(r"\b(good morning|gm|umaga na)\b", text):
        await update.message.reply_text("☀️ Good morning too!😏")
        return

    # ===== WHAT TIME =====
    if re.search(r"\b(anong oras naba?|time|What time is it?)\b", text):
        tz = pytz.timezone("Asia/Manila")
        now = datetime.now(tz)
        time_now = now.strftime("%I:%M %p")

        await update.message.reply_text(
            f"⏰ Time check: **{time_now}**",
            parse_mode="Markdown"
        )
        return

    if re.search(r"\b(ano ang pangalan mo|who are you)\b", text):
        await msg.reply_text("🤖 Ako si Kazebot! Bot na tumutulong sa channel na ito.")
        return

    # ===== FUN / RANDOM =====
    if re.search(r"\b(gg|good game)\b", text):
        await msg.reply_text("🎮 GG! Nice play!")
        return

    if re.search(r"\b(oops|oh no|uh oh)\b", text):
        await msg.reply_text("🤥 Ehh?")
        return

    if re.search(r"\bPalaro\b", text):
        await msg.reply_text("Mga kupal")
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

    # Get reporter info
    reporter_name = update.effective_user.full_name or update.effective_user.username

    # Confirm to reporter (member)
    await msg.reply_text("✅ Your report has been sent to the admins Owner.")

    # Get admins
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

import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= GLOBAL GAME STATE =================
picks = {}              # {user_id: [numbers]}
roll_enabled = True     # stoproll / runroll
pending_game = False    # may roll na walang nanalo

# ================= HELPER: CHECK ADMIN =================
async def is_admin(update, context):
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id
    )
    return member.status in ["administrator", "creator"]

# ================= PICK NUMBER (1–6, MAX 3, NO DUPLICATE) =================
async def pick_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global pending_game

    if pending_game:
        await update.message.reply_text(
            "⏳ May pending game pa. Hintayin muna matapos bago mag-pick ulit."
        )
        return

    text = update.message.text.strip()
    if text not in ["1", "2", "3", "4", "5", "6"]:
        return

    user = update.effective_user
    user_id = user.id
    number = int(text)

    # 🔴 CHECK DUPLICATE NUMBER (OTHER PLAYERS)
    for uid, nums in picks.items():
        if uid != user_id and number in nums:
            await update.message.reply_text(
                "❌ Bawal duplicate number, please palitan mo yung number mo."
            )
            return

    user_picks = picks.get(user_id, [])

    if len(user_picks) >= 3:
        await update.message.reply_text("❌ Max 3 numbers lang pwede mong piliin.")
        return

    if number in user_picks:
        await update.message.reply_text("⚠️ Napili mo na yan.")
        return

    user_picks.append(number)
    picks[user_id] = user_picks

    await update.message.reply_text(
        f"✅ {user.first_name}, picks mo: {user_picks}"
    )

# ================= CORE ROLL LOGIC =================
async def process_roll(update: Update, context: ContextTypes.DEFAULT_TYPE, is_reroll=False):
    global pending_game

    dice = random.randint(1, 6)
    winners = []

    for uid, nums in picks.items():
        if dice in nums:
            member = await context.bot.get_chat_member(
                update.effective_chat.id, uid
            )
            winners.append(member.user.mention_html())

    if winners:
        await update.message.reply_html(
            f"🎲 <b>{'Re' if is_reroll else ''}Rolled Number:</b> {dice}\n\n"
            f"🎯 <b>Result (Number {dice}):</b>\n"
            f"{'<br>'.join(winners)}\n\n"
            f"🎉 <b>WINNER(S)!</b>\n"
            f"📩 You win! DM @KAZEHAYAMODZ"
        )

        picks.clear()
        pending_game = False

    else:
        pending_game = True
        await update.message.reply_text(
            f"🎲 Rolled Number: {dice}\n"
            f"😢 Walang nanalo.\n\n"
            f"🔁 Gamitin ang /reroll para mag-roll ulit."
        )

# ================= /roll (ALL MEMBERS) =================
async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global roll_enabled, pending_game

    if not roll_enabled:
        await update.message.reply_text("⛔ Roll stop from admin or owner")
        return

    if pending_game:
        await update.message.reply_text(
            "⏳ May pending game pa. Gamitin ang /reroll."
        )
        return

    if not picks:
        await update.message.reply_text("❌ Walang sumali sa palaro.")
        return

    await process_roll(update, context, is_reroll=False)

# ================= /reroll (ALL MEMBERS) =================
async def reroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global pending_game

    if not pending_game:
        await update.message.reply_text(
            "❌ Walang pending game. Gamitin ang /roll."
        )
        return

    await process_roll(update, context, is_reroll=True)

# ================= /cancelroll (ADMIN & OWNER ONLY) =================
async def cancelroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global pending_game, picks

    if not await is_admin(update, context):
        return

    picks.clear()
    pending_game = False

    await update.message.reply_text(
        "🛑 Roll has been CANCELLED by admin.\n"
        "🔄 Game reset. Pwede na ulit mag-pick at /roll."
    )

# ================= /stoproll (ADMIN & OWNER ONLY) =================
async def stoproll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global roll_enabled

    if not await is_admin(update, context):
        return

    roll_enabled = False
    await update.message.reply_text("⛔ Roll has been STOPPED by admin/owner.")

# ================= /runroll (ADMIN & OWNER ONLY) =================
async def runroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global roll_enabled

    if not await is_admin(update, context):
        return

    roll_enabled = True
    await update.message.reply_text("▶️ Roll is now OPEN for all members!")

# ===== MAIN FUNCTION =====
def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")  # <-- siguraduhing kapareho sa Render env var
    if not token:
        raise RuntimeError("Missing TELEGRAM_TOKEN env var.")

    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("report", report_user))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, pick_number))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("stoproll", stoproll))
    app.add_handler(CommandHandler("runroll", runroll))
    app.add_handler(CommandHandler("reroll", reroll))
    app.add_handler(CommandHandler("cancelroll", cancelroll))
    
    # ===== STATUS UPDATES (welcome new members) =====
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_pogi))
    
    # Moderation
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.CAPTION | filters.FORWARDED) & ~filters.COMMAND,
            moderate
        )
    )

    app.run_polling(allowed_updates=Update.ALL_TYPES)

# ===== RUN =====
if __name__ == "__main__":
    keep_alive()
    main()


    
