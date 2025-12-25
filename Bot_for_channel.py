import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# From env vars sa Render
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID') or 0)  # Kung walang OWNER_ID, 0 lang

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Walang TELEGRAM_BOT_TOKEN sa env vars!")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Ako ang channel management bot mo.')

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(f'Maligayang pagdating, {member.full_name}! Enjoy sa channel! 🚀')

async def prevent_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.forward_origin:
        return

    user_id = message.from_user.id
    try:
        member = await context.bot.get_chat_member(message.chat.id, user_id)
        if member.status in ['administrator', 'creator'] or user_id == OWNER_ID:
            return  # Exempt admins & owner

        await message.delete()
        await context.bot.send_message(
            chat_id=message.chat.id,
            text=f'{message.from_user.full_name}, bawal mag-forward ng messages dito para sa regular members. 😊'
        )
    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL, prevent_forward))

    # Polling lang – walang webhook
    application.run_polling()

if __name__ == '__main__':
    main()
