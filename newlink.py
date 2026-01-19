import asyncio
import random
import string
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

PREFIX = "Kaze-"
active_keys = {}

OWNER_ID = int(os.getenv("OWNER_ID"))  # set on render environment

def generate_key(length=9):
    chars = string.ascii_letters + string.digits
    return PREFIX + ''.join(random.choice(chars) for _ in chars)

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

async def owner_check(update: Update):
    return update.effective_user.id == OWNER_ID

async def set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_check(update):
        return await update.message.reply_text("❌ Not allowed. Owner only.")

    args = context.args
    duration = timedelta(hours=12)

    if len(args) == 1:
        duration = parse_duration(args[0])

    key = generate_key()
    expire_time = datetime.now() + duration
    active_keys[key] = expire_time

    await update.message.reply_text(
        f"Generated key:\n\n`{key}`\n\nTap to copy 👆\nExpires in {duration}",
        parse_mode="Markdown"
    )

    asyncio.create_task(expire_key(key, update))

async def expire_key(key, update):
    remain = (active_keys[key] - datetime.now()).total_seconds()
    await asyncio.sleep(remain)
    del active_keys[key]
    await update.message.reply_text(f"❗ Key Expired: `{key}`", parse_mode="Markdown")

async def keys_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_check(update):
        return await update.message.reply_text("❌ Not allowed. Owner only.")

    if not active_keys:
        return await update.message.reply_text("No active keys.")

    msg = "Active Keys:\n\n"
    for k, t in active_keys.items():
        remain = t - datetime.now()
        minutes = int(remain.total_seconds() // 60)
        msg += f"`{k}` — {minutes}m remaining\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("set", set_cmd))
    app.add_handler(CommandHandler("keys", keys_cmd))

    print("BOT RUNNING ON RENDER...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
