from aiogram import Dispatcher

from .common import register_common_handlers
from .recipes import register_recipe_handlers
from .voice import register_voice_handlers # Убедись, что этот импорт есть

def register_all_handlers(dp: Dispatcher):
    """
    Регистрирует все обработчики в Диспетчере.
    Порядок регистрации определяет приоритет:
    1. Команды (самый высокий)
    2. Коллбэки (следующий)
    3. Голосовые сообщения
    4. Обычный текст (самый низкий)
    """
    
    # 1. КОМАНДЫ И КОЛЛБЭКИ (Общие, первыми перехватывают /start, /admin и кнопки)
    register_common_handlers(dp)
    
    # 2. ГОЛОСОВЫЕ СООБЩЕНИЯ (F.voice)
    register_voice_handlers(dp)
    
    # 3. ПРОСТОЙ ТЕКСТ (F.text - должен быть последним, чтобы не перехватывать команды)
    # register_recipe_handlers содержит F.text, который является фильтром по умолчанию.
    register_recipe_handlers(dp)