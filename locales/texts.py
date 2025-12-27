from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# --- Описания Премиума (Оставьте как были, для краткости опущу) ---
PREMIUM_DESC_EN = "💎 Premium Benefits..." 

BASE_EN = {
    # Языки
    "lang_ru": "🇷🇺 Russian", "lang_en": "🇬🇧 English", "lang_de": "🇩🇪 Deutsch",
    "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español",
    "choose_language": "🌐 **Choose Language:**",
    "lang_changed": "🌐 Language changed.",

    # Главное
    "welcome": """👋 **Welcome to FoodWizard.pro!**\n🥕 **Ingredients?**\nWrite list or speak.\n⚡️ **Or:** "Recipe for..." """,
    "welcome_gift_alert": "🎁 **Gift!** 7 Days Premium in 48h.",
    "menu": "🍴 **Main Menu**",
    "help_title": "❓ **Help**", "help_text": "Send ingredients.",
    
    # Кнопки
    "btn_favorites": "⭐️ Favorites", "btn_restart": "🔄 Restart", "btn_change_lang": "🌐 Language", 
    "btn_help": "❓ Help", "btn_back": "⬅️ Back", "btn_buy_premium": "💎 Premium",
    "btn_add_to_fav": "☆ Add", "btn_remove_from_fav": "🌟 Saved", "btn_another": "➡️ More",
    "favorites_title": "⭐️ **Favorites**", "favorites_empty": "😔 Empty.",
    
    # Лимиты и ошибки
    "premium_required_text": "Feature locked.", "limit_favorites_exceeded": "🔒 Limit 3.",
    "limit_voice_exceeded": "❌ Voice limit.", "limit_text_exceeded": "❌ Text limit.",
    "error_generation": "❌ Error.", "error_voice_recognition": "🗣️ Error.",
    "error_not_enough_products": "🤔 Need ingredients.",
    "promo_instruction": "ℹ️ Use: <code>/code ...</code>", "premium_description": PREMIUM_DESC_EN
}

TEXTS: Dict[str, Dict[str, str]] = {
    "en": BASE_EN.copy(),
    # Создаем словари для других языков. Скрипт внизу заполнит их из EN.
    "de": {}, "fr": {}, "it": {}, "es": {}
}

# --- FILL GAPS ---
base = TEXTS["en"]
for lang in ["de", "fr", "it", "es"]:
    if not TEXTS[lang]: TEXTS[lang] = {} # Инициализируем
    for k, v in base.items():
        if k not in TEXTS[lang]:
            TEXTS[lang][k] = v

def get_text(lang: str, key: str, **kwargs) -> str:
    # 1. Защита языка
    if lang not in TEXTS: lang = "en"
    # 2. Защита ключа
    text = TEXTS[lang].get(key, TEXTS["en"].get(key, "MISSING")) 
    
    if kwargs and text:
        try: return text.format(**kwargs)
        except: return text
    return text