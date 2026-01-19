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
import time
import os

PREFIX = "Kaze-"
active_keys = {}

OWNER_ID = int(os.getenv("OWNER_ID"))

def generate_key(length=9):
    chars = string.ascii_letters + string.digits
    return PREFIX + ''.join(random.choice(chars) for _ in range(length))

def parse_duration(arg: str) -> timedelta:
    num = int(''.join(filter(str.isdigit, arg)))
    unit = ''.join(filter(str.isalpha, arg)).lower()

    if unit == "m":
        return timedelta(minutes=num)
    elif unit == "h":
        return timedelta(hours=num)
    elif unit == "d":
        return timedelta(days=num)
    else:
        return timedelta(hours=12)

async def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID

async def set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_owner(update):
        return await update.message.reply_text("❌ Owner only.")

    args = context.args
    duration = timedelta(hours=12)

    if len(args) == 1:
        duration = parse_duration(args[0])

    key = generate_key()
    expire_time = datetime.now() + duration
    active_keys[key] = expire_time

    await update.message.reply_text(
        f"Generated:\n`{key}`\nTap to copy\nExpires in: {duration}",
        parse_mode="Markdown"
    )

    asyncio.create_task(expire_key(key, update))

async def expire_key(key, update):
    remain = (active_keys[key] - datetime.now()).total_seconds()
    await asyncio.sleep(remain)
    del active_keys[key]
    await update.message.reply_text(f"⛔ Expired: `{key}`", parse_mode="Markdown")

async def keys_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_owner(update):
        return await update.message.reply_text("❌ Owner only.")

    if not active_keys:
        return await update.message.reply_text("No active keys.")

    msg = "Active Keys:\n\n"
    for k, t in active_keys.items():
        remain = t - datetime.now()
        mins = int(remain.total_seconds() // 60)
        msg += f"`{k}` — {mins}m left\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("set", set_cmd))
    app.add_handler(CommandHandler("keys", keys_cmd))

    print("Bot running on Render...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
