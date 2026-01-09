import secrets
import string
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------- Configuration ----------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
RENTRY_SLUG = os.environ.get("RENTRY_SLUG")
edit_code = os.environ.get("RENTRY_EDIT_CODE")

if not TELEGRAM_TOKEN or not CHAT_ID or not RENTRY_SLUG or not edit_code:
    raise ValueError("Missing required env variables: TELEGRAM_TOKEN, CHAT_ID, RENTRY_SLUG, RENTRY_EDIT_CODE")

CHAT_ID = int(CHAT_ID)
RENTRY_URL = f"https://rentry.co/{RENTRY_SLUG}"
RAW_URL = f"{RENTRY_URL}/raw"

# Key settings
PREFIX = "Kaze-"
RANDOM_LENGTH_MIN = 6
RANDOM_LENGTH_MAX = 7
KEY_CHARS = string.ascii_letters + string.digits

current_interval_seconds = 60
job = None
default_interval_seconds = 60

# ---------------- Helpers ----------------
def generate_short_key():
    length = secrets.choice([RANDOM_LENGTH_MIN, RANDOM_LENGTH_MAX])
    return PREFIX + "".join(secrets.choice(KEY_CHARS) for _ in range(length))

def get_csrf_token(session):
    return session.get("https://rentry.co").cookies.get("csrftoken", None)

def update_paste_with_text(text):
    session = requests.Session()
    csrf = get_csrf_token(session)
    if not csrf:
        return False
    data = {"csrfmiddlewaretoken": csrf, "edit_code": edit_code, "text": text}
    headers = {"Referer": RENTRY_URL}
    res = session.post(f"{RENTRY_URL}/edit", data=data, headers=headers)
    if res.status_code == 200:
        return requests.get(RAW_URL).text.strip() == text
    return False

def parse_interval(text: str) -> int:
    text = text.lower().strip()
    try:
        if text.endswith("sec") or text.endswith("s"):
            return max(30, int(text[:-3 if text.endswith("sec") else -1]))
        elif text.endswith("min") or text.endswith("m"):
            return max(30, int(text[:-3 if text.endswith("min") else -1])) * 60
        elif text.endswith("hour") or text.endswith("h"):
            return int(text[:-4 if text.endswith("hour") else -1]) * 3600
        elif text.endswith("d"):
            return int(text[:-1]) * 86400
        return 60
    except:
        return 60

def parse_time_to_seconds(time_str: str) -> int:
    text = time_str.lower().strip()
    try:
        if text.endswith("s"): text = text[:-1]
        if text.endswith("sec"): return max(30, int(text[:-3]))
        elif text.endswith("min"): return max(30, int(text[:-3])) * 60
        elif text.endswith("hour"): return int(text[:-4]) * 3600
        elif text.endswith("h"): return int(text[:-1]) * 3600
        elif text.endswith("m"): return max(30, int(text[:-1])) * 60
        elif text.endswith("d"): return int(text[:-1]) * 86400
        else: return max(30, int(text))
    except:
        return default_interval_seconds

def update_key():
    new_key = generate_short_key()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success = update_paste_with_text(new_key)
    msg = "Success" if success else "Failed"
    return success, msg, new_key, timestamp

# ---------------- Async Handlers ----------------
async def create_and_send_new_key(context: ContextTypes.DEFAULT_TYPE):
    success, msg, new_key, timestamp = update_key()
    header = "✨ 𝙉𝙀𝙒 𝙐𝙋𝘿𝘼𝙏𝙀 𝙆𝙀𝙔 ✨"
    message = (
        f"{header}\n\n"
        f"💠 **Key Details:**\n"
        f"⏰ **Time:** `{timestamp}`\n"
        f"🔑 **𝗞𝗘𝗬:** `{new_key}`\n"
        f"📂 **Raw Link:** {RAW_URL}\n\n"
        "⚡ Use this key responsibly.\n"
        "💡 Tap the key to copy instantly!"
    )
    await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID: return
    msg = (
        "⚡ **ＫＥＹ ＭＥＮＵ ＣＥＮＴＥＲ** ⚡\n\n"
        f"📂 **Raw Link:** {RAW_URL}\n\n"
        "🛠️ Commands:\n"
        "/set <time> - Set interval\n"
        "/revoke - Generate new key\n"
        "/stop - Pause rotation\n"
        "/restart - Resume rotation\n"
        "/custom - Set custom key manually"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID: return
    if not context.args:
        await update.message.reply_text("Usage: /set 30sec or /set 1min")
        return
    global job, current_interval_seconds
    seconds = parse_interval(" ".join(context.args))
    current_interval_seconds = seconds
    if job: job.schedule_removal()
    job = context.job_queue.run_repeating(
        lambda ctx: context.application.create_task(create_and_send_new_key(ctx)),
        interval=seconds,
        first=seconds
    )
    await update.message.reply_text(f"✅ Interval set to every {seconds} seconds!")
    await create_and_send_new_key(context)

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID: return
    await create_and_send_new_key(context)

async def stop_rotation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID: return
    global job
    if job: job.schedule_removal(); job = None
    await update.message.reply_text("⏸️ Rotation paused! Use /restart to resume.")

async def restart_rotation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID: return
    global job, current_interval_seconds
    if job: job.schedule_removal()
    job = context.job_queue.run_repeating(
        lambda ctx: context.application.create_task(create_and_send_new_key(ctx)),
        interval=current_interval_seconds,
        first=10
    )
    await update.message.reply_text("▶️ Rotation resumed!")
    await create_and_send_new_key(context)

async def custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID: return
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /custom <your_key> <time>\nExample:\n/custom ABC123 30sec"
        )
        return
    custom_key = context.args[0]
    seconds = parse_time_to_seconds(" ".join(context.args[1:]))
    if seconds < 30:
        await update.message.reply_text("⚠️ Min 30sec required!")
        return
    timestamp = datetime.now().strftime("%H:%M:%S")
    message = (
        "𝗡𝗘𝗪 𝗖𝗨𝗦𝗧𝗢𝗠𝗘 𝗞𝗘𝗬\n\n"
        f"💠 **Key Details:**\n"
        f"⏰ **Time:** `{timestamp}`\n"
        f"🔑 **𝗞𝗘𝗬:** `{custom_key}`\n"
        f"📂 **Raw Link:** {RAW_URL}\n\n"
        "⚡ Use this key responsibly.\n"
        "💡 Tap the key to copy!"
    )
    await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
    if update_paste_with_text(custom_key):
        context.job_queue.run_once(
            lambda ctx: context.application.create_task(create_and_send_new_key(ctx)),
            when=seconds
        )

# ---------------- Main ----------------
async def on_startup(app: Application):
    # Schedule first key rotation safely
    app.job_queue.run_once(
        lambda ctx: app.create_task(create_and_send_new_key(ctx)),
        when=10
    )

def main():
    keep_alive()
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(on_startup).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_interval))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("stop", stop_rotation))
    app.add_handler(CommandHandler("restart", restart_rotation))
    app.add_handler(CommandHandler("custom", custom))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
