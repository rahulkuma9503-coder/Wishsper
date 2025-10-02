import os
import logging
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.filters import CommandStart

from .config import settings
from .db import db
from .handlers.inline import handle_inline_query
from .handlers.callbacks import handle_show_whisper, CallbackFilter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Register handlers
dp.inline_query()(handle_inline_query)
dp.callback_query(CallbackFilter("show_"))(handle_show_whisper)

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer(
        "🤫 Welcome to Whisper Bot!\n\n"
        "Send secret messages in any chat using inline mode:\n\n"
        "Type: @BotUsername your_message @target_user\n\n"
        "Example: @BotUsername Hello, this is secret! @username"
    )

# FastAPI app
app = FastAPI(title="Telegram Whisper Bot")

@app.on_event("startup")
async def on_startup():
    await db.connect()
    
    # Set webhook
    webhook_url = f"{settings.WEBHOOK_BASE_URL}/webhook/{settings.BOT_TOKEN}"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")

@app.on_event("shutdown")
async def on_shutdown():
    await db.close()
    await bot.session.close()

@app.post("/webhook/{token}")
async def webhook_handler(token: str, request: Request):
    if token != settings.BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    update = Update(**await request.json())
    await dp.feed_update(bot, update)
    
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "Bot is running", "service": "Telegram Whisper Bot"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
