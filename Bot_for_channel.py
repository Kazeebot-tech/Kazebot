import os
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# ===== WEBKEEP ALIVE =====
app_web = Flask(__name__)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

@app_web.route("/")
def home():
    return "Bot is online!"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app_web.run(host="0.0.0.0", port=port)).start()
    
# ===== ENV FROM RENDER =====
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# ==========================

async def is_admin_or_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat

    if user.id == OWNER_ID:
        return True

    member = await context.bot.get_chat_member(chat.id, user.id)
    return member.status in ("administrator", "creator")

async def anti_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    # ✅ allow owner & admins
    if await is_admin_or_owner(update, context):
        return

    text = (message.text or "").lower()

    # ❌ BLOCK FORWARDED
    if message.forward_date:
        await message.delete()
        await context.bot.send_message(
            chat_id=message.chat.id,
            text="🚫 No forward allowed!"
        )
        return

    # ❌ BLOCK t.me LINKS
    if "t.me/" in text:
        await message.delete()
        await context.bot.send_message(
            chat_id=message.chat.id,
            text="🚫 No ads / links allowed!"
        )
        return

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, anti_ads)
    )

    print("🤖 Anti-Forward Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
