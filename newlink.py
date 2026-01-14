import os
import random
import string
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Store keys & expiry
active_keys = {}

def generate_key():
    length = random.randint(8, 10)
    chars = string.ascii_letters + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(length))
    return f"Kaze_{random_part}"

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = generate_key()
    await update.message.reply_text(f"Generated Key:\n`{key}`", parse_mode="Markdown")

def parse_duration(text):
    num = ''.join([c for c in text if c.isdigit()])
    unit = ''.join([c for c in text if c.isalpha()])

    if not num: return None
    num = int(num)

    if unit in ["m", "min", "mins"]:
        return timedelta(minutes=num)
    if unit in ["h", "hr", "hrs"]:
        return timedelta(hours=num)
    if unit in ["d", "day", "days"]:
        return timedelta(days=num)

    return None

async def expire_task(context, key, user_id, duration):
    await asyncio.sleep(duration.total_seconds())
    if key in active_keys:
        del active_keys[key]
        await context.bot.send_message(chat_id=user_id, text=f"⏰ Key expired: `{key}`", parse_mode="Markdown")

async def set_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/set 12h <key>`", parse_mode="Markdown")
        return

    duration_text = context.args[0]
    key = context.args[1]

    duration = parse_duration(duration_text)
    if not duration:
        await update.message.reply_text("Invalid duration. Example: `10min`, `2h`, `1d`", parse_mode="Markdown")
        return

    expires_at = datetime.now() + duration
    active_keys[key] = expires_at

    user_id = update.effective_chat.id
    await update.message.reply_text(f"Key `{key}` set for {duration_text}.", parse_mode="Markdown")

    # run expiration
    asyncio.create_task(expire_task(context, key, user_id, duration))

async def list_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not active_keys:
        await update.message.reply_text("No active keys.")
        return

    msg = "Active keys:\n"
    for k, exp in active_keys.items():
        msg += f"- `{k}` expires at {exp.strftime('%H:%M:%S')}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online")

async def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(CommandHandler("set", set_key))
    app.add_handler(CommandHandler("keys", list_keys))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
