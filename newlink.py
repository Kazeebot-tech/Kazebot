import os
import logging
import secrets
import string
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID"))
RENTRY_SLUG = os.environ.get("RENTRY_SLUG")
RENTRY_URL = f"https://rentry.co/{RENTRY_SLUG}"
RAW_URL = f"https://rentry.co/{RENTRY_SLUG}/raw"
edit_code = os.environ.get("RENTRY_EDIT_CODE")

# Key generation settings
PREFIX = "Kaze-"
RANDOM_LENGTH_MIN = 6
RANDOM_LENGTH_MAX = 7
KEY_CHARS = string.ascii_letters + string.digits

current_interval_seconds = 60
job = None

def generate_short_key():
    length = secrets.choice([RANDOM_LENGTH_MIN, RANDOM_LENGTH_MAX])
    random_part = ''.join(secrets.choice(KEY_CHARS) for _ in range(length))
    return PREFIX + random_part  # Kaze- + random

def get_csrf_token(session):
    response = session.get('https://rentry.co')
    if 'csrftoken' in response.cookies:
        return response.cookies['csrftoken']
    return None

def update_key():
    new_key = generate_short_key()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    session = requests.Session()
    csrf_token = get_csrf_token(session)
    if not csrf_token:
        return False, "CSRF error", new_key, timestamp

    data = {
        "csrfmiddlewaretoken": csrf_token,
        "edit_code": edit_code,
        "text": new_key
    }
    headers = {"Referer": RENTRY_URL}
    response = session.post(f"{RENTRY_URL}/edit", data=data, headers=headers)

    if response.status_code == 200:
        check = requests.get(RAW_URL).text.strip()
        if check == new_key:
            return True, "Success", new_key, timestamp
    return False, f"Failed (HTTP {response.status_code})", new_key, timestamp
    
from datetime import datetime

async def create_and_send_new_key(context: ContextTypes.DEFAULT_TYPE):
    success, msg, new_key, timestamp = update_key()
    
    # Current date for header
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Fancy header fonts
    header = f"✨ 𝙉𝙀𝙒 𝙐𝙋𝘿𝘼𝙏𝙀 𝙆𝙀𝙔 ✨"
    
    # Single static message (same format always)
    message = (
        f"{header}\n\n"
        f"💠 **Key Details:**\n"
        f"⏰ **Time:** `{timestamp}`\n"
        f"🔑 **𝗞𝗘𝗬:** `{new_key}`\n"
        f"📂 **Raw Link:** {RAW_URL}\n\n"
        f"⚡ Use this key responsibly.\n"
        f"💡 Tip: Tap the key to copy instantly!"
    )

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode="Markdown"
    )

def parse_interval(text: str) -> int:
    text = text.lower().strip()
    try:
        if text.endswith('sec') or text.endswith('s'):
            return max(30, int(text[:-3 if text.endswith('sec') else -1]))
        elif text.endswith('min') or text.endswith('m'):
            return max(30, int(text[:-3 if text.endswith('min') else -1])) * 60
        elif text.endswith('hour') or text.endswith('h'):
            return int(text[:-4 if text.endswith('hour') else -1]) * 3600
        elif text.endswith('d'):
            return int(text[:-1]) * 86400
        return 60
    except:
        return 60

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "⚡ **ＫＥＹ ＭＥＮＵ ＣＥＮＴＥＲ** ⚡\n\n"
        f"📂 **Raw Link:** {RAW_URL}\n\n"
        "🛠️ **Commands:**\n"
        "/set <time> - Set a custom interval\n"
        "/revoke - revoke old key generate a new key\n"
        "/stop - Stop the key scheduler\n"
        "/restart - Restart the system\n"
        "/custom - Set a custom key manually\n"
    )

    await update.message.reply_text(
        message,
        parse_mode="Markdown"
    )

async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    if not context.args:
        await update.message.reply_text('Usage: /set 30sec or /set 1min')
        return
    seconds = parse_interval(' '.join(context.args))
    global current_interval_seconds, job
    current_interval_seconds = seconds
    if job:
        job.schedule_removal()
    job = context.job_queue.run_repeating(create_and_send_new_key, interval=seconds, first=seconds)
    await update.message.reply_text(f'✅ Set to every {seconds}sec!')
    await create_and_send_new_key(context)

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    await create_and_send_new_key(context)

async def stop_rotation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    global is_running, job
    is_running = False
    if job:
        job.schedule_removal()
        job = None
    await update.message.reply_text('⏸️ Rotation paused! Use /restart to resume.')

async def restart_rotation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    global is_running, job
    is_running = True
    if job:
        job.schedule_removal()
    job = context.job_queue.run_repeating(create_and_send_new_key, interval=current_interval_seconds, first=10)
    await update.message.reply_text('▶️ Rotation resumed!')
    await create_and_send_new_key(context)

def parse_time_to_seconds(time_str: str) -> int:
    time_str = time_str.lower().strip()
    try:
        if time_str.endswith('sec') or time_str.endswith('s'):
            return max(30, int(time_str[:-3 if time_str.endswith('sec') else -1]))
        elif time_str.endswith('min') or time_str.endswith('m'):
            return max(30, int(time_str[:-3 if time_str.endswith('min') else -1])) * 60
        elif time_str.endswith('hour') or time_str.endswith('h'):
            return int(time_str[:-4 if time_str.endswith('hour') else -1]) * 3600
        elif time_str.endswith('d'):
            return int(time_str[:-1]) * 86400
        return default_interval_seconds
    except:
        return default_interval_seconds

async def custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            'Usage: /custom <your_key> <time>\n'
            'Example:\n'
            '/custom SuperPogi123 30sec\n'
            '/custom KazeMaster 1min\n'
            '/custom MyPass 1hour\n'
            '/custom DailyKey 1d'
        )
        return
    
    custom_key = context.args[0]
    time_str = ' '.join(context.args[1:])
    seconds = parse_time_to_seconds(time_str)
    
    if seconds < 30:
        await update.message.reply_text('⚠️ Min 30sec dai para sa custom!')
        return
    
    # Human-readable duration for the message
    secs = seconds
    if secs >= 86400:
        days = secs // 86400
        duration_str = f"{days} day{'s' if days > 1 else ''}"
    elif secs >= 3600:
        hours = secs // 3600
        duration_str = f"{hours} hour{'s' if hours > 1 else ''}"
    elif secs >= 60:
        mins = secs // 60
        duration_str = f"{mins} minute{'s' if mins > 1 else ''}"
    else:
        duration_str = f"{secs} second{'s' if secs > 1 else ''}"
    
    # Always send the clean success message
    timestamp = datetime.now().strftime("%H:%M:%S")
    message = (
        f"𝗡𝗘𝗪 𝗖𝗨𝗦𝗧𝗢𝗠𝗘 𝗞𝗘𝗬\n\n"
        f"💠 **Key Details:**\n"
        f"⏰ **Time:** `{timestamp}`\n"
        f"🔑 **𝗞𝗘𝗬:** `{custom_key}`\n"
        f"📂 **Raw Link:** {RAW_URL}\n\n"
        f"⚡ Use this key responsibly.\n"
        f"💡 Tip: Tap the key to copy instantly!"
    )

    await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
    
    # Try to set the custom key
    success = update_paste_with_text(custom_key)
    
    # If successful, schedule revert to random
    if success:
        context.job_queue.run_once(
            do_random_update,
            when=seconds,
            name="revert_to_random"
        )

def parse_time_to_seconds(time_str: str) -> int:
    time_str = time_str.lower().strip()
    try:
        # Remove trailing 's' if present (for plural)
        if time_str.endswith('s'):
            time_str = time_str[:-1]
        
        # Parse based on ending
        if time_str.endswith('sec'):
            return max(30, int(time_str[:-3]))
        elif time_str.endswith('min'):
            return max(30, int(time_str[:-3])) * 60
        elif time_str.endswith('hour'):
            return int(time_str[:-4]) * 3600
        elif time_str.endswith('h'):
            return int(time_str[:-1]) * 3600
        elif time_str.endswith('m'):
            return max(30, int(time_str[:-1])) * 60
        elif time_str.endswith('d'):
            return int(time_str[:-1]) * 86400
        else:
            # Just number = seconds
            return max(30, int(time_str))
    except:
        return default_interval_seconds

def update_paste_with_text(text):
    session = requests.Session()
    csrf_token = get_csrf_token(session)
    if not csrf_token:
        return False
    
    data = {
        'csrfmiddlewaretoken': csrf_token,
        'edit_code': edit_code,
        'text': text
    }
    headers = {'Referer': RENTRY_URL}
    response = session.post(f'{RENTRY_URL}/edit', data=data, headers=headers)
    
    if response.status_code == 200:
        check = requests.get(RAW_URL).text.strip()
        if check == text:
            return True
    return False

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.job_queue.run_once(create_and_send_new_key, 10)
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('set', set_interval))
    app.add_handler(CommandHandler('revoke', revoke))
    app.add_handler(CommandHandler('stop', stop_rotation))
    app.add_handler(CommandHandler('restart', restart_rotation))
    app.add_handler(CommandHandler('custom', custom))
 
    print("Bot is running")
    app.run_polling()

if __name__ == '__main__':
    main()
