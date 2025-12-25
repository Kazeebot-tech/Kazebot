import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Kunin ang token at owner ID mula sa environment variables (sa Render)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID'))  # Siguraduhing integer ito

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Walang TELEGRAM_BOT_TOKEN sa environment variables!")
if not OWNER_ID:
    raise ValueError("Walang OWNER_ID sa environment variables!")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! Ako ang channel management bot mo.')

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for member in update.message.new_chat_members:
        await update.message.reply_text(f'Maligayang pagdating, {member.full_name}! Enjoy sa channel! 🚀')

async def prevent_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return

    # Check kung forwarded message (v20+ uses message.forward_origin)
    if message.forward_origin:
        user_id = message.from_user.id

        try:
            member = await context.bot.get_chat_member(message.chat.id, user_id)
            # Exempt admins, creator (owner ng chat), at ikaw (OWNER_ID)
            if member.status in ['administrator', 'creator'] or user_id == OWNER_ID:
                return  # Allow

            # Delete ang forwarded message
            await message.delete()
            # Optional warning
            await context.bot.send_message(
                chat_id=message.chat.id,
                text=f'{message.from_user.full_name}, bawal mag-forward ng messages dito para sa regular members. 😊'
            )
        except Exception as e:
            logger.error(f"Error sa prevent_forward: {e}")

def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL, prevent_forward))

    # Run with polling (perfect for Background Worker)
    application.run_polling()

if __name__ == '__main__':
    main()
