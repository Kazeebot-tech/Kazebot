import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import re

# Function to handle /start command
async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    update.message.reply_text(f"Hello, {user.first_name}! Welcome to the bot. Type /help for more info.")

# Function to handle /owner command (restricted to OWNER_ID)
async def owner(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id == int(os.getenv("OWNER_ID")):  # Check if the user is the owner
        update.message.reply_text(f"Hello Owner {update.message.from_user.first_name}, you have full access!")
    else:
        update.message.reply_text("You are not authorized to use this command.")

# Function to check if user is the owner or admin
async def is_admin(update: Update, context: CallbackContext) -> bool:
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id

    # Get chat admins
    admins = await context.bot.get_chat_administrators(chat_id)
    
    # Check if the user is the owner or an admin
    for admin in admins:
        if admin.user.id == user_id or user_id == int(os.getenv("OWNER_ID")):
            return True
    return False

# Function to block forwarded messages (exclude owner and admins)
async def block_forwarded(update: Update, context: CallbackContext) -> None:
    user_is_admin = await is_admin(update, context)
    if update.message.forward_from and not user_is_admin:
        await update.message.delete()  # Delete forwarded message
        await update.message.reply_text("Forwarding messages is not allowed for non-admins!")

# Function to detect t.me links and block them (exclude owner and admins)
async def block_tme_links(update: Update, context: CallbackContext) -> None:
    user_is_admin = await is_admin(update, context)
    if update.message.text:
        if re.search(r't\.me', update.message.text) and not user_is_admin:  # Check if there's a t.me link
            await update.message.delete()  # Delete the message
            await update.message.reply_text("Links to t.me are not allowed for non-admins!")

# Main function to set up the bot
async def main():
    # Get the bot token and owner ID from the environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    owner_id = os.getenv("OWNER_ID")

    if not bot_token or not owner_id:
        raise ValueError("Environment variables TELEGRAM_BOT_TOKEN or OWNER_ID are not set.")
    
    # Create the application object with the token from the environment
    application = Application.builder().token(bot_token).build()

    # Add handler for /start command
    application.add_handler(CommandHandler("start", start))

    # Add handler for /owner command (restricted to OWNER_ID)
    application.add_handler(CommandHandler("owner", owner))

    # Add handler for forwarded messages (only block for non-admins)
    application.add_handler(MessageHandler(filters.FORWARDED, block_forwarded))

    # Add handler for messages with t.me links (only block for non-admins)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, block_tme_links))

    # Start the Bot
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())  # Running the main function with asyncio
