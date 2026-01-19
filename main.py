import os
import random
import string
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from decouple import config

# ENV VARIABLES
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
OWNER_ID = int(config('OWNER_ID'))  # Only owner can use /set

# Store active keys
active_keys = {}

# Generate random key
def generate_key(length=10):
    chars = string.ascii_letters + string.digits
    return 'Kaze-' + ''.join(random.choice(chars) for _ in range(length))

# Expire key after time
async def expire_key(key: str, duration: timedelta, update: Update):
    await asyncio.sleep(duration.total_seconds())
    if key in active_keys:
        del active_keys[key]
        await update.message.reply_text(f"❌ Key expired: `{key}`", parse_mode="Markdown")

# /set command
async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("⛔ Only the owner can use this command.")

    # Default duration: 12 hours
    duration = timedelta(hours=12)

    if context.args:
        arg = context.args[0]
        if arg[-1] in ['m','h','d']:
            value = int(arg[:-1])
            unit = arg[-1]
            if unit == 'm': duration = timedelta(minutes=value)
            elif unit == 'h': duration = timedelta(hours=value)
            elif unit == 'd': duration = timedelta(days=value)
        else:
            return await update.message.reply_text("Invalid duration. Use 1m, 1h, 1d.")

    key = generate_key(10)
    active_keys[key] = datetime.now() + duration

    await update.message.reply_text(
        f"✅ New Key:\n`{key}`\nExpires in: {arg if context.args else '12h'}\n(Tap to copy)",
        parse_mode="Markdown"
    )

    # Schedule expiration
    asyncio.create_task(expire_key(key, duration, update))

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online ✅")

# Main function
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_command))

    print("Bot running on Render...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
