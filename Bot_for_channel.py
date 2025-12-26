import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import re

# Function to handle /start command
def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    update.message.reply_text(f"Hello, {user.first_name}! Welcome to the bot. Type /help for more info.")

# Function to handle /owner command (restricted to OWNER_ID)
def owner(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id == int(os.getenv("OWNER_ID")):  # Check if the user is the owner
        update.message.reply_text(f"Hello Owner {update.message.from_user.first_name}, you have full access!")
    else:
        update.message.reply_text("You are not authorized to use this command.")

# Function to block forwarded messages
def block_forwarded(update: Update, context: CallbackContext) -> None:
    if update.message.forward_from:
        update.message.delete()  # Delete forwarded message
        update.message.reply_text("Forwarding messages is not allowed!")

# Function to detect t.me links and block them
def block_tme_links(update: Update, context: CallbackContext) -> None:
    if update.message.text:
        if re.search(r't\.me', update.message.text):  # Check if there's a t.me link
            update.message.delete()  # Delete the message
            update.message.reply_text("Links to t.me are not allowed!")

# Main function to set up the bot
def main():
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

    # Add handler for forwarded messages
    application.add_handler(MessageHandler(filters.FORWARDED, block_forwarded))

    # Add handler for messages with t.me links
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, block_tme_links))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
