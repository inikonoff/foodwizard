import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# ===== API КЛЮЧИ =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# ===== АДМИНИСТРАТОРЫ =====
ADMIN_IDS: List[int] = [] 
# Пример: ADMIN_IDS = [123456789]

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

SUPPORTED_LANGUAGES = ["ru", "en", "de", "fr", "it", "es"]
DEFAULT_LANGUAGE = "ru"

# ===== ЛИМИТЫ (БАЛАНС v1.1) =====
FREE_USER_LIMITS = {
    "daily_requests": 10,     # 10 текстовых (хватит на день)
    "voice_per_day": 1,       # 1 голосовой (тест-драйв)
    "max_favorites": 3        # "Мягкий" лимит избранного
}

PREMIUM_USER_LIMITS = {
    "daily_requests": 100,
    "voice_per_day": 50,
    "max_favorites": 1000     # Практически безлимит
}

# ===== ТРИАЛ =====
TRIAL_DELAY_HOURS = 48    # Выдать через 2 дня
TRIAL_DURATION_DAYS = 7   # На неделю

# ===== ЛОГГИРОВАНИЕ =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "bot.log"

def validate_config():
    if not TELEGRAM_TOKEN or not GROQ_API_KEY or not DATABASE_URL:
        raise ValueError("Не установлены обязательные переменные окружения")