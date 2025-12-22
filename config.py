import os
from dotenv import load_dotenv
from typing import List

# Загружаем переменные окружения
load_dotenv()

# Для совместимости с гибридным main.py
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

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

# !!! ВАЖНО: Переменная должна существовать, даже если она пустая !!!
ADMIN_IDS: List[int] = [] 

# Если вы хотите вернуть админов, раскомментируйте блок ниже:
# admin_str = os.getenv("ADMIN_IDS", "")
# if admin_str:
#     for admin_id in admin_str.split(","):
#         admin_id = admin_id.strip()
#         if admin_id.isdigit():
#             ADMIN_IDS.append(int(admin_id))

# Секретный код для активации премиума
SECRET_PROMO_CODE = os.getenv("SECRET_PROMO_CODE", "FOOD2025")

# ===== МОДЕЛИ И НАСТРОЙКИ LLM =====
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "1000"))

# ===== ДИРЕКТОРИИ И ФАЙЛЫ =====
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/chef_bot")

# ===== НАСТРОЙКИ КЭША =====
CACHE_TTL_RECIPE = int(os.getenv("CACHE_TTL_RECIPE", "3600"))
CACHE_TTL_ANALYSIS = int(os.getenv("CACHE_TTL_ANALYSIS", "86400"))
CACHE_TTL_VALIDATION = int(os.getenv("CACHE_TTL_VALIDATION", "86400"))
CACHE_TTL_INTENT = int(os.getenv("CACHE_TTL_INTENT", "86400"))
CACHE_TTL_DISH_LIST = int(os.getenv("CACHE_TTL_DISH_LIST", "3600"))

# ===== НАСТРОЙКИ ИНТЕРФЕЙСА =====
FAVORITES_PER_PAGE = int(os.getenv("FAVORITES_PER_PAGE", "5"))

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

def validate_config():
    errors = []
    if not TELEGRAM_TOKEN: errors.append("TELEGRAM_TOKEN")
    if not GROQ_API_KEY: errors.append("GROQ_API_KEY")
    if not DATABASE_URL: errors.append("DATABASE_URL")
    
    if errors:
        raise ValueError(f"Отсутствуют необходимые переменные окружения: {', '.join(errors)}")
