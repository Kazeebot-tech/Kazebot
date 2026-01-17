from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import os
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
SERVER_URL = os.environ.get("BASE_URL")  # e.g., https://kazebot-4jkt.onrender.com

updater = Updater(BOT_TOKEN)

def ban(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Usage: /ban DEVICE_ID")
        return
    device = context.args[0]
    r = requests.get(f"{SERVER_URL}/ban?device={device}")
    update.message.reply_text(r.text)

def check(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Usage: /check DEVICE_ID")
        return
    device = context.args[0]
    r = requests.get(f"{SERVER_URL}/check?device={device}")
    update.message.reply_text(f"Device {device}: {r.text}")

updater.dispatcher.add_handler(CommandHandler("ban", ban))
updater.dispatcher.add_handler(CommandHandler("check", check))

updater.start_polling()
updater.idle()
