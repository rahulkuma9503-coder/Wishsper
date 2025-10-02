import os
import logging
from fastapi import FastAPI, Request, HTTPException
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext, InlineQueryHandler, CallbackQueryHandler, MessageHandler, filters
from pymongo import MongoClient
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "en")

# MongoDB setup
client = MongoClient(MONGODB_URI)
db = client.whisper_bot
whispers = db.whispers

# Initialize bot
application = Application.builder().token(BOT_TOKEN).build()

# Language strings
LANGUAGES = {
    "en": {
        "usage": "Usage: @BotUsername secret_text @username",
        "whisper_placeholder": "🔒 A whisper message to {target_username} — Only they can open it.",
        "show_message": "show message 🔒",
        "secret_sent": "Secret sent to your DM 🔐",
        "not_for_you": "This whisper is only for @{target_username}",
    },
    "hi": {
        "usage": "उपयोग: @BotUsername गुप्त_संदेश @username",
        "whisper_placeholder": "🔒 @{target_username} को एक गुप्त संदेश — केवल वे इसे खोल सकते हैं।",
        "show_message": "संदेश दिखाएं 🔒",
        "secret_sent": "आपके DM में संदेश भेज दिया गया है 🔐",
        "not_for_you": "यह संदेश केवल @{target_username} के लिए है",
    }
}

async def handle_inline_query(update: Update, context: CallbackContext):
    query = update.inline_query.query.strip()
    user = update.inline_query.from_user
    user_lang = user.language_code or DEFAULT_LANG
    if user_lang not in LANGUAGES:
        user_lang = DEFAULT_LANG
    
    # Parse query
    pattern = r'^(.*?)\s*@(\w+)$'
    match = re.match(pattern, query)
    
    if not match or not query:
        # Show usage help
        await update.inline_query.answer([{
            'type': 'article',
            'id': 'help',
            'title': 'Whisper Bot Usage',
            'input_message_content': {
                'message_text': LANGUAGES[user_lang]["usage"]
            },
            'description': LANGUAGES[user_lang]["usage"]
        }])
        return
    
    secret_text = match.group(1).strip()
    target_username = match.group(2).strip()
    
    if not secret_text:
        await update.inline_query.answer([{
            'type': 'article',
            'id': 'error',
            'title': 'Empty Message',
            'input_message_content': {
                'message_text': LANGUAGES[user_lang]["usage"]
            },
            'description': 'Please provide a secret message'
        }])
        return
    
    # Create whisper in database
    whisper_data = {
        "whisper_id": str(update.inline_query.id),
        "from_user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        },
        "target_username": target_username.lower().replace("@", ""),
        "secret_text": secret_text,
        "created_at": datetime.utcnow(),
        "opened_at": None,
        "opened_by": None
    }
    
    whispers.insert_one(whisper_data)
    
    # Create inline keyboard
    keyboard = [[InlineKeyboardButton(
        LANGUAGES[user_lang]["show_message"], 
        callback_data=f"show_{update.inline_query.id}"
    )]]
    
    await update.inline_query.answer([{
        'type': 'article',
        'id': update.inline_query.id,
        'title': f'Whisper to @{target_username}',
        'input_message_content': {
            'message_text': LANGUAGES[user_lang]["whisper_placeholder"].format(
                target_username=target_username
            )
        },
        'reply_markup': InlineKeyboardMarkup(keyboard),
        'description': 'Click to send whisper'
    }])

async def handle_callback_query(update: Update, context: CallbackContext):
    query = update.callback_query
    whisper_id = query.data.replace("show_", "")
    user = query.from_user
    user_lang = user.language_code or DEFAULT_LANG
    if user_lang not in LANGUAGES:
        user_lang = DEFAULT_LANG
    
    # Find whisper in database
    whisper = whispers.find_one({"whisper_id": whisper_id})
    
    if not whisper:
        await query.answer("Whisper not found or expired", show_alert=True)
        return
    
    target_username = whisper["target_username"]
    
    # Check if user is the target
    is_target = (user.username and 
                user.username.lower() == target_username.lower())
    
    if is_target:
        try:
            await context.bot.send_message(
                user.id,
                f"🔓 Secret message from @{whisper['from_user'].get('username', 'Unknown')}:\n\n{whisper['secret_text']}"
            )
            whispers.update_one(
                {"whisper_id": whisper_id},
                {"$set": {"opened_at": datetime.utcnow(), "opened_by": user.id}}
            )
            await query.answer(LANGUAGES[user_lang]["secret_sent"])
        except Exception as e:
            await query.answer("Please start a DM with me first", show_alert=True)
    else:
        await query.answer(
            LANGUAGES[user_lang]["not_for_you"].format(target_username=target_username),
            show_alert=True
        )

# Add handlers
application.add_handler(InlineQueryHandler(handle_inline_query))
application.add_handler(CallbackQueryHandler(handle_callback_query, pattern="^show_"))

# FastAPI app
app = FastAPI(title="Telegram Whisper Bot")

@app.on_event("startup")
async def on_startup():
    # Set webhook
    webhook_url = f"{WEBHOOK_BASE_URL}/webhook"
    await application.bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")

@app.post("/webhook")
async def webhook_handler(request: Request):
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "Bot is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
