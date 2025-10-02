from aiogram import types
from aiogram.filters import Filter
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..config import settings, LANGUAGES
from ..db import db

class CallbackFilter(Filter):
    def __init__(self, startswith: str):
        self.startswith = startswith
    
    async def __call__(self, callback: types.CallbackQuery):
        return callback.data.startswith(self.startswith)

async def handle_show_whisper(callback: types.CallbackQuery):
    whisper_id = callback.data.replace("show_", "")
    user_id = callback.from_user.id
    user_lang = callback.from_user.language_code or settings.DEFAULT_LANG
    if user_lang not in LANGUAGES:
        user_lang = settings.DEFAULT_LANG
    
    whisper = await db.get_whisper(whisper_id)
    
    if not whisper:
        await callback.answer("Whisper not found or expired", show_alert=True)
        return
    
    target_username = whisper["target_username"]
    
    # Check if user is the target
    is_target = (callback.from_user.username and 
                callback.from_user.username.lower() == target_username.lower())
    
    if is_target:
        # Send secret via DM
        from ..main import bot
        
        try:
            await bot.send_message(
                user_id,
                f"🔓 Secret message from @{whisper['from_user'].get('username', 'Unknown')}:\n\n{whisper['secret_text']}"
            )
            await db.mark_whisper_opened(whisper_id, user_id)
            await callback.answer(LANGUAGES[user_lang]["secret_sent"])
        except Exception as e:
            await callback.answer("Please start a DM with me first", show_alert=True)
    else:
        await callback.answer(
            LANGUAGES[user_lang]["not_for_you"].format(target_username=target_username),
            show_alert=True
        )
