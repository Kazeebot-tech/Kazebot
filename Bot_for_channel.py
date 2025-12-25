import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Validation
if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN!")
if not OWNER_ID or not CHANNEL_ID:
    raise RuntimeError("Missing OWNER_ID or CHANNEL_ID!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command sa channel"""
    if update.effective_chat.id != CHANNEL_ID:
        return

    user = update.effective_user
    first_name = user.first_name or "Ka-Skit"

    welcome_text = f"""
Hi {first_name}! 👋

Welcome sa **KazeSkit Giveaway Collective**! 🎉

Dito tayo mag-enjoy sa mga legit giveaways at updates! 

⚠️ Reminder lang ha:
• Bawal mag-forward ng messages
• Bawal maglagay ng t.me links (except admins)

Para clean at safe lagi ang channel natin! 🔒

Good luck sa mga giveaways, sana manalo ka! 🔥
    """
    await update.message.reply_text(welcome_text.strip())

async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Block forwards and t.me links from non-admins"""
    message = update.effective_message
    if message.chat_id != CHANNEL_ID:
        return

    user_id = update.effective_user.id

    # Owner always allowed
    if user_id == OWNER_ID:
        return

    # Get admins
    admins = await context.bot.get_chat_administrators(CHANNEL_ID)
    admin_ids = [admin.user.id for admin in admins]

    # Admins allowed
    if user_id in admin_ids:
        return

    # BLOCK 1: Forwarded messages
    if message.forward_from or message.forward_from_chat or message.forward_date:
        await message.delete()
        print(f"Deleted forwarded message from {user_id}")
        return

    # BLOCK 2: t.me links
    text = (message.text or message.caption or "").lower()
    if "t.me/" in text:
        await message.delete()
        print(f"Deleted message with t.me link from {user_id}")

def main():
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))

    # Moderation: text, caption, forwarded (hindi commands)
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.CAPTION | filters.FORWARDED) & ~filters.COMMAND,
            moderate
        )
    )

    # Start the bot
    print("Bot is starting...")
    print(f"Monitoring channel: {CHANNEL_ID}")
    print(f"Owner ID: {OWNER_ID}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
