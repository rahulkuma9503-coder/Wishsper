import re
from datetime import datetime
from aiogram import F, types
from aiogram.filters import Command
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..config import settings, LANGUAGES
from ..db import db

async def handle_inline_query(inline_query: InlineQuery):
    query = inline_query.query.strip()
    user_lang = inline_query.from_user.language_code or settings.DEFAULT_LANG
    if user_lang not in LANGUAGES:
        user_lang = settings.DEFAULT_LANG
    
    # Parse query: "secret message @username"
    pattern = r'^(.*?)\s*@(\w+)$'
    match = re.match(pattern, query)
    
    if not match or not query:
        # Show usage help
        result = InlineQueryResultArticle(
            id="help",
            title="Whisper Bot Usage",
            description=LANGUAGES[user_lang]["usage"],
            input_message_content=InputTextMessageContent(
                message_text=LANGUAGES[user_lang]["usage"]
            )
        )
        await inline_query.answer([result], cache_time=1)
        return
    
    secret_text = match.group(1).strip()
    target_username = match.group(2).strip()
    
    if not secret_text:
        result = InlineQueryResultArticle(
            id="error",
            title="Empty Message",
            description="Please provide a secret message",
            input_message_content=InputTextMessageContent(
                message_text=LANGUAGES[user_lang]["usage"]
            )
        )
        await inline_query.answer([result], cache_time=1)
        return
    
    # Create whisper in database
    from_user = {
        "id": inline_query.from_user.id,
        "username": inline_query.from_user.username,
        "first_name": inline_query.from_user.first_name,
        "last_name": inline_query.from_user.last_name
    }
    
    whisper_id = db.create_whisper(from_user, target_username, secret_text)
    
    # Send admin copy
    await send_admin_copy(from_user, target_username, secret_text, user_lang)
    
    # Create inline result
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=LANGUAGES[user_lang]["show_message"], callback_data=f"show_{whisper_id}")
    
    result = InlineQueryResultArticle(
        id=whisper_id,
        title=f"Whisper to @{target_username}",
        description=f"Click to send whisper",
        input_message_content=InputTextMessageContent(
            message_text=LANGUAGES[user_lang]["whisper_placeholder"].format(
                target_username=target_username
            )
        ),
        reply_markup=keyboard.as_markup()
    )
    
    await inline_query.answer([result], cache_time=1)

async def send_admin_copy(from_user: dict, target_username: str, secret_text: str, lang: str):
    from ..main import bot
    
    admin_message = LANGUAGES[lang]["admin_copy"].format(
        from_username=from_user.get("username", "No username"),
        target_username=target_username,
        time=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    )
    
    admin_message += f"\nMessage: {secret_text}"
    
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_message)
        except Exception as e:
            print(f"Failed to send admin copy to {admin_id}: {e}")
