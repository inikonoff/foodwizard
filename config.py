import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_IDS: List[int] = []

SECRET_PROMO_CODE = os.getenv("SECRET_PROMO_CODE", "TRIAL99")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "1000"))
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/chef_bot")

# Кэш
CACHE_TTL_RECIPE = 3600
CACHE_TTL_ANALYSIS = 86400
CACHE_TTL_VALIDATION = 86400
CACHE_TTL_INTENT = 86400
CACHE_TTL_DISH_LIST = 3600

FAVORITES_PER_PAGE = int(os.getenv("FAVORITES_PER_PAGE", "5"))

# !!! ИЗМЕНЕНИЕ: УБРАН RU, ДЕФОЛТ EN !!!
SUPPORTED_LANGUAGES = ["en", "de", "fr", "it", "es"]
DEFAULT_LANGUAGE = "en"

# Лимиты
FREE_USER_LIMITS = {
    "daily_requests": 10,
    "voice_per_day": 1,
    "max_favorites": 3  # Мягкий лимит
}

PREMIUM_USER_LIMITS = {
    "daily_requests": 100,
    "voice_per_day": 50,
    "max_favorites": 1000
}

TRIAL_DELAY_HOURS = 48
TRIAL_DURATION_DAYS = 7

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "bot.log"

def validate_config():
    if not TELEGRAM_TOKEN or not GROQ_API_KEY or not DATABASE_URL:
        raise ValueError("Critical env vars missing")