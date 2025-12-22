from aiogram import Dispatcher

from .common import register_common_handlers
from .recipes import register_recipe_handlers
from .voice import register_voice_handlers
from .favorites import register_favorites_handlers # <--- ИМПОРТ

def register_all_handlers(dp: Dispatcher):
    """
    Регистрирует все обработчики в Диспетчере.
    """
    
    # 1. Команды
    register_common_handlers(dp)
    
    # 2. Избранное
    register_favorites_handlers(dp)
    
    # 3. Голос
    register_voice_handlers(dp)
    
    # 4. Текст (последний)
    register_recipe_handlers(dp)
