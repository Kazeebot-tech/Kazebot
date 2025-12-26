from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import re

# Function to handle /start command
def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    update.message.reply_text(f"Hello, {user.first_name}! Welcome to the bot. Type /help for more info.")

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
    # Replace 'YOUR_TOKEN' with your bot's API token
    updater = Updater("YOUR_TOKEN")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add handler for /start command
    dispatcher.add_handler(CommandHandler("start", start))

    # Add handler for forwarded messages
    dispatcher.add_handler(MessageHandler(Filters.forwarded, block_forwarded))

    # Add handler for messages with t.me links
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, block_tme_links))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
