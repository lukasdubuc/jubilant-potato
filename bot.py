import nest_asyncio
import os
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ✅ Prevent async issues (Important for Railway)
nest_asyncio.apply()

# ✅ Set up Flask server to keep Railway active
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# ✅ Get Bot Token & Password from Environment Variables
TOKEN = os.getenv("BOT_TOKEN")  # Retrieves token from Railway Variables
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD")  # Retrieves password from Railway Variables

# ✅ Track authenticated users & pending password requests
authorized_users = set()
pending_password_request = set()

# ✅ Chatbot responses
def chatbot_response(user_input):
    responses = {
        "hi": "Hello! How can I assist you today?",
        "hello": "Hey there! What’s on your mind?",
        "how are you": "I'm just an AI, but I'm doing great! How about you?",
        "what can you do": "I can chat, help with business automation, and assist with product creation. Some features require a password.",
        "who are you": "I'm your AI assistant, here to help you manage and grow your business!",
    }
    return responses.get(user_input.lower(), "I'm here to chat! Let me know how I can help.")

# ✅ Start Command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "👋 Hello! I'm your AI assistant.\n"
        "💬 You can chat with me freely.\n"
        "🔒 Some advanced features require a password.\n"
        "If you need business automation or product creation, type `/auth` to enter the password."
    )

# ✅ Request Password
async def request_password(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id in authorized_users:
        await update.message.reply_text("✅ You are already authorized!")
        return

    pending_password_request.add(user_id)
    await update.message.reply_text("🔑 Please enter the password:")

# ✅ Check Password
async def check_password(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_text = update.message.text.strip()

    if user_id not in pending_password_request:
        await chat(update, context)  # ✅ Redirect to normal chat
        return  

    if user_text == ACCESS_PASSWORD:
        authorized_users.add(user_id)
        pending_password_request.remove(user_id)  
        await update.message.reply_text("✅ Access granted! You can now use advanced features.")
    else:
        await update.message.reply_text("❌ Incorrect password. Try again.")

# ✅ Advanced Services (Requires Password)
async def advanced_services(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id not in authorized_users:
        await update.message.reply_text("🔒 You need to enter the password first. Type `/auth` to enter it.")
        return

    await update.message.reply_text("🚀 Advanced services are available! What would you like to do today?")

# ✅ Chat Function
async def chat(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id in pending_password_request:
        return  

    user_text = update.message.text.strip()
    response = chatbot_response(user_text)
    await update.message.reply_text(response)

# ✅ Initialize Telegram Bot
bot_app = Application.builder().token(TOKEN).build()

# ✅ Add Handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("auth", request_password))
bot_app.add_handler(CommandHandler("services", advanced_services))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("Bot is running...")

# ✅ Run Flask & Telegram Bot
import threading
import asyncio

def run_flask():
    app.run(host="0.0.0.0", port=5000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

asyncio.get_event_loop().run_until_complete(bot_app.run_polling())
