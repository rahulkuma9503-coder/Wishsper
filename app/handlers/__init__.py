"""
Handlers package for Telegram Whisper Bot.
Contains inline query handlers and callback handlers.
"""

from .inline import handle_inline_query
from .callbacks import handle_show_whisper

__all__ = ['handle_inline_query', 'handle_show_whisper']
