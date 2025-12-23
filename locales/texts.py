import os
from dotenv import load_dotenv
from typing import List

# Загружаем переменные окружения
load_dotenv()

# Для совместимости
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# ===== API КЛЮЧИ =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не установлен")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY не установлен")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не установлен")

# ===== АДМИНИСТРАТОРЫ =====
# Оставляем список пустым, чтобы вы могли тестировать лимиты как обычный пользователь
ADMIN_IDS: List[int] = [] 

SECRET_PROMO_CODE = os.getenv("SECRET_PROMO_CODE", "FOOD2025")

# ===== НАСТРОЙКИ LLM =====
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "1000"))
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/chef_bot")

# ===== КЭШ =====
CACHE_TTL_RECIPE = 3600
CACHE_TTL_ANALYSIS = 86400
CACHE_TTL_VALIDATION = 86400
CACHE_TTL_INTENT = 86400
CACHE_TTL_DISH_LIST = 3600

# ===== НАСТРОЙКИ ИНТЕРФЕЙСА =====
FAVORITES_PER_PAGE = int(os.getenv("FAVORITES_PER_PAGE", "5"))

# !!! ВАЖНО: ПОЛНЫЙ СПИСОК ЯЗЫКОВ !!!
SUPPORTED_LANGUAGES = ["ru", "en", "de", "fr", "it", "es"]
DEFAULT_LANGUAGE = "ru"

# ===== ЛИМИТЫ =====
FREE_USER_LIMITS = {
    "daily_requests": 10,
    "voice_per_day": 3,
    "max_ingredients": 10
}

PREMIUM_USER_LIMITS = {
    "daily_requests": 100,
    "voice_per_day": 50,
    "max_ingredients": 50
}

# ===== ЛОГГИРОВАНИЕ =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "bot.log"

def validate_config():
    if not TELEGRAM_TOKEN or not GROQ_API_KEY or not DATABASE_URL:
        raise ValueError("Не установлены обязательные переменные")