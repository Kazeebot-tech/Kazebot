from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
import random
import string
import asyncio
import os

OWNER_ID = int(os.getenv("OWNER_ID"))  # ilalagay mo sa Render env
PREFIX = "Kaze-"
active_keys = {}

def generate_key(length=10):
    chars = string.ascii_letters + string.digits
    return PREFIX + ''.join(random.choice(chars) for _ in range(length))

async def check_expiry(update: Update, key: str, exp_time):
    now = datetime.now()
    wait = (exp_time - now).total_seconds()
    await asyncio.sleep(wait)
    
    if key in active_keys and active_keys[key] == exp_time:
        del active_keys[key]
        await update.message.reply_text(f"❌ Key expired: `{key}`", parse_mode="Markdown")

async def set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
        return await update.message.reply_text("⛔ Owner only.")
    
    if len(context.args) == 0:
        return await update.message.reply_text("Usage: /set <1m|10m|1h|12h|1d>")

    duration = context.args[0]
    unit = duration[-1]
    value = int(duration[:-1])

    if unit == "m":
        expire = timedelta(minutes=value)
    elif unit == "h":
        expire = timedelta(hours=value)
    elif unit == "d":
        expire = timedelta(days=value)
    else:
        return await update.message.reply_text("Invalid unit (m,h,d)")

    key = generate_key()
    exp_time = datetime.now() + expire
    active_keys[key] = exp_time

    await update.message.reply_text(
        f"✅ Generated Key:\n`{key}`\n\n"
        f"⏳ Expires in: {duration}\n"
        f"(Tap to copy)",
        parse_mode="Markdown"
    )

    asyncio.create_task(check_expiry(update, key, exp_time))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot ready 🟢")

async def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_cmd))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
