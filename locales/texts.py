from typing import Dict, Any

TEXTS: Dict[str, Dict[str, str]] = {}

# --- БАЗОВЫЙ АНГЛИЙСКИЙ (ИСТОЧНИК) ---
EN_TEXTS = {
    "lang_ru": "🇷🇺 Russian", "lang_en": "🇬🇧 English", "lang_de": "🇩🇪 Deutsch",
    "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español",
    "choose_language": "🌐 **Choose Language:**",
    "lang_changed": "🌐 Language changed to English.",
    
    "welcome": """👋 **Welcome to FoodWizard.pro!**\n\n🥕 **Have ingredients?**\nDictate or write them.\n\n⚡️ **Or say:**\n"Give me a recipe for [dish]\"""",
    "menu": "🍴 **Main Menu**",
    "processing": "⏳ Thinking...",
    
    "btn_favorites": "⭐️ Favorites", "btn_restart": "🔄 Restart", "btn_change_lang": "🌐 Language",
    "btn_help": "❓ Help", "btn_add_to_fav": "☆ Add to Favorites", "btn_remove_from_fav": "🌟 In Favorites",
    "btn_back": "⬅️ Back", "btn_another": "➡️ Another Recipe", "btn_buy_premium": "💎 Get Premium",
    
    "favorites_title": "⭐️ **Favorites**", "favorites_empty": "😔 List is empty.",
    
    "premium_description": "💎 **Premium:** Unlimited, Nutrition facts, 100 requests.",
    "welcome_gift_alert": "🎁 **Gift!** 7 Days Premium soon.",
    "trial_activated_notification": "🎁 **Premium Activated!** Enjoy.",
    
    "limit_voice_exceeded": "❌ Voice limit!", "limit_text_exceeded": "❌ Text limit!",
    "error_voice_recognition": "🗣️ Error.", "error_generation": "❌ Error.",
    "error_not_enough_products": "🤔 Need ingredients.", "voice_recognized": "✅ Recognized: {text}",
    
    "soup": "🍜 Soups", "main": "🥩 Main", "salad": "🥗 Salads", "breakfast": "🥞 Breakfast", 
    "dessert": "🍰 Desserts", "drink": "🍹 Drinks", "snack": "🥨 Snacks",
    "choose_category": "📝 **Category:**", "choose_dish": "🍳 **Dish:**",
    "promo_instruction": "ℹ️ Code: /code ...", "help_title": "Help", "help_text": "Text..."
}

# --- ЯВНОЕ ЗАПОЛНЕНИЕ ВСЕХ ЯЗЫКОВ ---
# Мы копируем английский для всех, КРОМЕ специфичных вещей, если они будут
TEXTS["en"] = EN_TEXTS.copy()
TEXTS["de"] = EN_TEXTS.copy()
TEXTS["fr"] = EN_TEXTS.copy()
TEXTS["it"] = EN_TEXTS.copy()
TEXTS["es"] = EN_TEXTS.copy()

# ПРИМЕР: Можете переопределить только одно поле для теста:
# TEXTS["de"]["lang_changed"] = "🌐 Sprache geändert."

def get_text(lang: str, key: str, **kwargs) -> str:
    # 1. Защита языка
    if lang not in TEXTS: 
        lang = "en"
        
    lang_dict = TEXTS[lang]
    
    # 2. Защита ключа
    text = lang_dict.get(key, TEXTS["en"].get(key, key))
    
    if kwargs and text:
        try: return text.format(**kwargs)
        except: return text
    return text