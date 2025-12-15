from aiogram import Dispatcher
from .common import register_common_handlers
from .recipes import register_recipe_handlers
from .favorites import register_favorites_handlers
from .voice import register_voice_handlers

def register_all_handlers(dp: Dispatcher):
    """¥£¨áâà¨àã¥â ¢á¥ ®¡à ¡®âç¨ª¨"""
    register_common_handlers(dp)
    register_recipe_handlers(dp)
    register_favorites_handlers(dp)
    register_voice_handlers(dp)
