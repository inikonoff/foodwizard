import os
from dotenv import load_dotenv
from typing import List

# ‡ £àã¦ ¥¬ ¯¥à¥¬¥­­ë¥ ®ªàã¦¥­¨ï
load_dotenv()

# ===== API Š‹ž—ˆ =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN ­¥ ãáâ ­®¢«¥­ ¢ ¯¥à¥¬¥­­ëå ®ªàã¦¥­¨ï")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY ­¥ ãáâ ­®¢«¥­ ¢ ¯¥à¥¬¥­­ëå ®ªàã¦¥­¨ï")

# ===== €‡€ „€›• =====
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL ­¥ ãáâ ­®¢«¥­ ¢ ¯¥à¥¬¥­­ëå ®ªàã¦¥­¨ï")

# ===== €„Œˆˆ‘’€’Ž› ˆ …‡Ž€‘Ž‘’œ =====
# à¥®¡à §ã¥¬ áâà®ªã "123,456" ¢ á¯¨á®ª [123, 456]
ADMIN_IDS: List[int] = []
admin_str = os.getenv("ADMIN_IDS", "")
if admin_str:
    for admin_id in admin_str.split(","):
        admin_id = admin_id.strip()
        if admin_id.isdigit():
            ADMIN_IDS.append(int(admin_id))

# ‘¥ªà¥â­ë© ª®¤ ¤«ï  ªâ¨¢ æ¨¨ ¯à¥¬¨ã¬ 
SECRET_PROMO_CODE = os.getenv("SECRET_PROMO_CODE", "FOOD2025")

# ===== ŒŽ„…‹œ GROQ =====
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2000"))

# ===== €‘’Ž‰Šˆ Š˜€ =====
# ‚à¥¬ï ¦¨§­¨ ªíè  ¢ á¥ªã­¤ å
CACHE_TTL_RECIPE = int(os.getenv("CACHE_TTL_RECIPE", "86400"))  # 24 ç á 
CACHE_TTL_ANALYSIS = int(os.getenv("CACHE_TTL_ANALYSIS", "7200"))  # 2 ç á 
CACHE_TTL_VALIDATION = int(os.getenv("CACHE_TTL_VALIDATION", "1800"))  # 30 ¬¨­ãâ

# ===== €‘’Ž‰Šˆ ˆ‹Ž†…ˆŸ =====
# ‚à¥¬¥­­ ï ¤¨à¥ªâ®à¨ï
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/chef_bot")
os.makedirs(TEMP_DIR, exist_ok=True)

# Œ ªá¨¬ «ì­®¥ ª®«¨ç¥áâ¢® á®®¡é¥­¨© ¢ ¨áâ®à¨¨
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))

# ˆ§¡à ­­®¥ ­  áâà ­¨æã
FAVORITES_PER_PAGE = int(os.getenv("FAVORITES_PER_PAGE", "5"))

# ®¤¤¥à¦¨¢ ¥¬ë¥ ï§ëª¨ (¢ ¯®àï¤ª¥ ¯à¨®à¨â¥â )
SUPPORTED_LANGUAGES = ["ru", "en", "de", "fr", "it", "es"]
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "ru")

# ===== Žƒ€ˆ—…ˆŸ „‹Ÿ Ž‹œ‡Ž‚€’…‹…‰ =====
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

# ===== ‹ŽƒƒˆŽ‚€ˆ… =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

# ===== Ž‚…Š€ ŠŽ”ˆƒ“€–ˆˆ =====
def validate_config():
    """à®¢¥àï¥â ª®àà¥ªâ­®áâì ª®­ä¨£ãà æ¨¨"""
    errors = []
    
    if not TELEGRAM_TOKEN:
        errors.append("TELEGRAM_TOKEN ­¥ ãáâ ­®¢«¥­")
    
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY ­¥ ãáâ ­®¢«¥­")
    
    if not DATABASE_URL:
        errors.append("DATABASE_URL ­¥ ãáâ ­®¢«¥­")
    
    if DEFAULT_LANGUAGE not in SUPPORTED_LANGUAGES:
        errors.append(f"DEFAULT_LANGUAGE ¤®«¦¥­ ¡ëâì ®¤­¨¬ ¨§: {SUPPORTED_LANGUAGES}")
    
    if errors:
        raise ValueError(f"Žè¨¡ª¨ ª®­ä¨£ãà æ¨¨:\n" + "\n".join(errors))

# à®¢¥àï¥¬ ª®­ä¨£ãà æ¨î ¯à¨ ¨¬¯®àâ¥
validate_config()
