from aiogram import Dispatcher

from .common import register_common_handlers
from .recipes import register_recipe_handlers
from .voice import register_voice_handlers
from .favorites import register_favorites_handlers # <--- ДОБАВЛЕН ИМПОРТ

def register_all_handlers(dp: Dispatcher):
    """
    Регистрирует все обработчики в Диспетчере.
    Порядок регистрации важен!
    """
    
    # 1. Команды и общее меню (включая /start, /favorites)
    register_common_handlers(dp)
    
    # 2. Логика избранного (кнопки пагинации, добавления/удаления)
    register_favorites_handlers(dp)
    
    # 3. Голосовые сообщения
    register_voice_handlers(dp)
    
    # 4. Текстовые сообщения и генерация рецептов (F.text ловит все остальное)
    register_recipe_handlers(dp)
