import os
import asyncio
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

TOKEN = os.getenv("BOT_TOKEN")
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD")
DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-project.railway.app")

if not TOKEN or not ACCESS_PASSWORD:
    logger.error("Missing BOT_TOKEN or ACCESS_PASSWORD")
    raise ValueError("Required environment variables not set")

authorized_users = set()
pending_password_request = set()
bot_active = False
bot_app = None

@app.route('/')
def home():
    return "AI Business Hub is running!"

def chatbot_response(user_input):
    responses = {
        "hi": "Hello! How can I assist you today?",
        "hello": "Hey there! What’s on your mind?",
        "how are you": "I'm an AI hub, always ready! How about you?",
        "what can you do": "I manage your business! Use `/auth` for advanced features.",
        "who are you": "I'm your AI Business Hub, here to streamline your work!"
    }
    return responses.get(user_input.lower(), "How can I assist your business today?")

async def startbot(update: Update, context: CallbackContext):
    global bot_active
    bot_active = True
    await update.message.reply_text("✅ AI Hub active! Chat or use `/auth`.")
    logger.info("Bot activated")

async def stopbot(update: Update, context: CallbackContext):
    global bot_active
    bot_active = False
    await update.message.reply_text("❌ AI Hub deactivated. Use `/startbot`.")
    logger.info("Bot deactivated")

async def request_password(update: Update, context: CallbackContext):
    if not bot_active:
        return
    user_id = update.message.from_user.id
    if user_id in authorized_users:
        await update.message.reply_text("✅ Already authorized!")
        return
    pending_password_request.add(user_id)
    await update.message.reply_text("🔑 Enter the password:")

async def check_password(update: Update, context: CallbackContext):
    if not bot_active:
        return
    user_id = update.message.from_user.id
    user_text = update.message.text.strip()
    if user_id not in pending_password_request:
        await chat(update, context)
        return
    if user_text == ACCESS_PASSWORD:
        authorized_users.add(user_id)
        pending_password_request.remove(user_id)
        await update.message.reply_text("✅ Access granted! Use `/services`.")
        logger.info(f"User {user_id} authorized")
    else:
        await update.message.reply_text("❌ Wrong password. Try again.")
        logger.warning(f"Failed password attempt by {user_id}")

async def advanced_services(update: Update, context: CallbackContext):
    if not bot_active:
        return
    user_id = update.message.from_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("🔒 Use `/auth` to unlock.")
        return
    await update.message.reply_text("🚀 Advanced services ready! What’s next?")

async def chat(update: Update, context: CallbackContext):
    if not bot_active:
        return
    user_text = update.message.text.strip()
    response = chatbot_response(user_text)
    await update.message.reply_text(response)

async def init_bot():
    global bot_app
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("startbot", startbot))
    bot_app.add_handler(CommandHandler("stopbot", stopbot))
    bot_app.add_handler(CommandHandler("auth", request_password))
    bot_app.add_handler(CommandHandler("services", advanced_services))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    webhook_url = f"https://{DOMAIN}/webhook"
    try:
        await bot_app.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to {webhook_url}")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
    return bot_app

@app.route('/webhook', methods=['POST'])
def webhook():
    if bot_app is None:
        logger.error("Bot not initialized")
        return "Bot not ready", 503
    try:
        update = Update.de_json(request.get_json(), bot_app.bot)
        asyncio.run_coroutine_threadsafe(bot_app.process_update(update), asyncio.get_event_loop())
        return "OK"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(init_bot())
    except Exception as e:
        logger.error(f"Bot initialization failed: {e}")
        raise

    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)
