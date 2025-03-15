import nest_asyncio
import os
import asyncio
import threading
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ✅ Prevent async issues with nested event loops
nest_asyncio.apply()

# ✅ Configure logging for debugging and monitoring
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ✅ Set up Flask server (keeps the app alive on platforms like Railway)
app = Flask(__name__)

@app.route('/')
def home():
    return "AI Business Hub is ready but inactive until started via Telegram."

# ✅ Load environment variables
TOKEN = os.getenv("BOT_TOKEN")
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD")

if not TOKEN or not ACCESS_PASSWORD:
    logger.error("BOT_TOKEN or ACCESS_PASSWORD not set in environment variables.")
    raise ValueError("Missing required environment variables.")

# ✅ Global state management
class HubState:
    def __init__(self):
        self.authorized_users = set()          # Tracks users with access
        self.pending_password_request = set()  # Tracks users awaiting password
        self.bot_active = False                # Bot starts inactive

state = HubState()

# ✅ Chatbot response logic (expandable for future AI features)
def chatbot_response(user_input):
    responses = {
        "hi": "Hello! How can I assist you today?",
        "hello": "Hey there! What’s on your mind?",
        "how are you": "I'm an AI hub, always ready to help! How about you?",
        "what can you do": "I'm the central hub for your business! I can chat, manage worker bots, and unlock advanced features with a password.",
        "who are you": "I'm Grok 3, your AI business hub, built by xAI to streamline your operations!"
    }
    return responses.get(user_input.lower(), "I’m here to assist! How can I support your business today?")

# ✅ Command: Start the bot
async def startbot(update: Update, context: CallbackContext):
    state.bot_active = True
    await update.message.reply_text("✅ AI Business Hub is now active! Use `/auth` for advanced features or chat with me.")
    logger.info("Bot activated.")

# ✅ Command: Stop the bot
async def stopbot(update: Update, context: CallbackContext):
    state.bot_active = False
    await update.message.reply_text("❌ AI Business Hub deactivated. Use `/startbot` to reactivate.")
    logger.info("Bot deactivated.")

# ✅ Handle chat messages (only when bot is active)
async def chat(update: Update, context: CallbackContext):
    if not state.bot_active:
        return  # Ignore if bot is inactive

    user_text = update.message.text.strip()
    response = chatbot_response(user_text)
    await update.message.reply_text(response)
    logger.info(f"Chat response sent: {response}")

# ✅ Command: Request password for authorization
async def request_password(update: Update, context: CallbackContext):
    if not state.bot_active:
        return  # Ignore if bot is inactive

    user_id = update.message.from_user.id
    if user_id in state.authorized_users:
        await update.message.reply_text("✅ You’re already authorized!")
        return

    state.pending_password_request.add(user_id)
    await update.message.reply_text("🔑 Please enter the password:")
    logger.info(f"Password requested by user {user_id}")

# ✅ Check password input
async def check_password(update: Update, context: CallbackContext):
    if not state.bot_active:
        return  # Ignore if bot is inactive

    user_id = update.message.from_user.id
    user_text = update.message.text.strip()

    if user_id not in state.pending_password_request:
        await chat(update, context)  # Treat as normal chat message
        return

    if user_text == ACCESS_PASSWORD:
        state.authorized_users.add(user_id)
        state.pending_password_request.remove(user_id)
        await update.message.reply_text("✅ Access granted! Use `/services` for advanced features.")
        logger.info(f"User {user_id} authorized.")
    else:
        await update.message.reply_text("❌ Incorrect password. Try again.")
        logger.warning(f"Failed password attempt by user {user_id}")

# ✅ Command: Access advanced services (placeholder for worker bot integration)
async def advanced_services(update: Update, context: CallbackContext):
    if not state.bot_active:
        return  # Ignore if bot is inactive

    user_id = update.message.from_user.id
    if user_id not in state.authorized_users:
        await update.message.reply_text("🔒 Authorization required. Use `/auth` to enter the password.")
        return

    await update.message.reply_text("🚀 Welcome to advanced services! Options:\n1. Manage worker bots\n2. Analyze data\n3. Automate tasks\nWhat would you like to do?")
    logger.info(f"User {user_id} accessed advanced services.")

# ✅ Initialize Telegram bot
async def init_bot():
    bot_app = Application.builder().token(TOKEN).build()

    # Add command and message handlers
    bot_app.add_handler(CommandHandler("startbot", startbot))
    bot_app.add_handler(CommandHandler("stopbot", stopbot))
    bot_app.add_handler(CommandHandler("auth", request_password))
    bot_app.add_handler(CommandHandler("services", advanced_services))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logger.info("Bot initialized, starting polling...")
    await bot_app.run_polling()

# ✅ Run Flask server in a separate thread
def run_flask():
    logger.info("Starting Flask server...")
    app.run(host="0.0.0.0", port=5000, debug=False)

# ✅ Main execution
if __name__ == "__main__":
    # Start Flask in a thread to keep the app alive
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True  # Ensures Flask stops when main thread exits
    flask_thread.start()

    # Run the Telegram bot
    try:
        asyncio.run(init_bot())
    except Exception as e:
        logger.error(f"Error running bot: {e}")
