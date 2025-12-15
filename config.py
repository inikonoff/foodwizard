import os
from dotenv import load_dotenv
from typing import List

# Загружаем переменные окружения
load_dotenv()

# ===== API КЛЮЧИ =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не установлен в переменных окружения")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY не установлен в переменных окружения")

# ===== БАЗА ДАННЫХ =====
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не установлен в переменных окружения")

# ===== АДМИНИСТРАТОРЫ И БЕЗОПАСНОСТЬ =====
# Преобразуем строку "123,456" в список [123, 456]
ADMIN_IDS: List[int] = []
admin_str = os.getenv("ADMIN_IDS", "")
if admin_str:
    for admin_id in admin_str.split(","):
        admin_id = admin_id.strip()
        if admin_id.isdigit():
            ADMIN_IDS.append(int(admin_id))

# Секретный код для активации премиума
SECRET_PROMO_CODE = os.getenv("SECRET_PROMO_CODE", "FOOD2025")

# ===== МОДЕЛЬ GROQ =====
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2000"))

# ===== НАСТРОЙКИ КЭША =====
# Время жизни кэша в секундах
CACHE_TTL_RECIPE = int(os.getenv("CACHE_TTL_RECIPE", "86400"))  # 24 часа
CACHE_TTL_ANALYSIS = int(os.getenv("CACHE_TTL_ANALYSIS", "7200"))  # 2 часа
CACHE_TTL_VALIDATION = int(os.getenv("CACHE_TTL_VALIDATION", "1800"))  # 30 минут

# ===== НАСТРОЙКИ ПРИЛОЖЕНИЯ =====
# Временная директория
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/chef_bot")
os.makedirs(TEMP_DIR, exist_ok=True)

# Максимальное количество сообщений в истории
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))

# Избранное на страницу
FAVORITES_PER_PAGE = int(os.getenv("FAVORITES_PER_PAGE", "5"))

# Поддерживаемые языки (в порядке приоритета)
SUPPORTED_LANGUAGES = ["ru", "en", "de", "fr", "it", "es"]
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "ru")

# ===== ОГРАНИЧЕНИЯ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ =====
FREE_USER_LIMITS = {
    "daily_requests": int(os.getenv("FREE_DAILY_REQUESTS", "10")),
    "voice_per_day": int(os.getenv("FREE_VOICE_PER_DAY", "3")),
    "max_ingredients": int(os.getenv("FREE_MAX_INGREDIENTS", "10"))
}

PREMIUM_USER_LIMITS = {
    "daily_requests": int(os.getenv("PREMIUM_DAILY_REQUESTS", "100")),
    "voice_per_day": int(os.getenv("PREMIUM_VOICE_PER_DAY", "50")),
    "max_ingredients": int(os.getenv("PREMIUM_MAX_INGREDIENTS", "50"))
}

# ===== ЛОГГИРОВАНИЕ =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

# ===== ПРОВЕРКА КОНФИГУРАЦИИ =====
def validate_config():
    """Проверяет корректность конфигурации"""
    errors = []
    
    if not TELEGRAM_TOKEN:
        errors.append("TELEGRAM_TOKEN не установлен")
    
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY не установлен")
    
    if not DATABASE_URL:
        errors.append("DATABASE_URL не установлен")
    
    if DEFAULT_LANGUAGE not in SUPPORTED_LANGUAGES:
        errors.append(f"DEFAULT_LANGUAGE должен быть одним из: {SUPPORTED_LANGUAGES}")
    
    if errors:
        raise ValueError(f"Ошибки конфигурации:\n" + "\n".join(errors))

# Проверяем конфигурацию при импорте
validate_config()
