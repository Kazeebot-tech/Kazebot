import os
import random
import string
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from decouple import config  # optional, kung gusto mo dotenv

# Accessing Telegram bot token and chat ID from environment variables
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
CHAT_ID = config('CHAT_ID')

# Dictionary para sa mga active keys at expiration times
active_keys = {}

# Function para mag-generate ng random key
def generate_key(length):
    letters_and_digits = string.ascii_letters + string.digits
    return 'Kaze-' + ''.join(random.choice(letters_and_digits) for i in range(length))

# Function para sa /set command
def set_command(update: Update, context: CallbackContext):
    key = generate_key(10)
    expiration_time = time.time() + 12*60*60  # 12 oras expiration time
    active_keys[key] = expiration_time
    update.message.reply_text(f"New key generated: {key}. Tap to copy.")

# Function para mag-check ng expiration ng keys
def check_expiration():
    current_time = time.time()
    expired_keys = [key for key, exp_time in active_keys.items() if current_time >= exp_time]
    
    for key in expired_keys:
        del active_keys[key]
        # I-send ang notification sa user na expired na ang key
        
# Main function
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("set", set_command))
    
    updater.start_polling()
    
    # Loop para mag-check ng expiration ng keys
    while True:
        check_expiration()
        time.sleep(60)  # Check every minute
        
    updater.idle()

if __name__ == '__main__':
    main()
