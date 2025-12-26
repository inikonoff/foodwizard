from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# --- ОПИСАНИЯ ПРЕМИУМА ---
PREMIUM_DESC_EN = """💎 **Premium Benefits:**...""" # Оставьте описания как есть
PREMIUM_DESC_DE = """💎 **Premium-Vorteile:**..."""
PREMIUM_DESC_FR = """💎 **Avantages Premium :**..."""
PREMIUM_DESC_IT = """💎 **Vantaggi Premium:**..."""
PREMIUM_DESC_ES = """💎 **Beneficios Premium:**..."""

# Основной английский словарь (Источник правды)
BASE_EN = {
    # --- Categories (KEYS MUST MATCH PROMPTS) ---
    "soup": "🍜 Soups", 
    "main": "🥩 Main Courses", 
    "salad": "🥗 Salads", 
    "breakfast": "🥞 Breakfasts", 
    "dessert": "🍰 Desserts", 
    "drink": "🍹 Drinks", 
    "snack": "🥨 Snacks",
    
    # --- UI ---
    "welcome": """👋 **Welcome to FoodWizard.pro!**\n\n🎤 Dictate or write ingredients.\n⚡️ Or say: "Give me a recipe for [dish]\"""",
    "start_manual": "", 
    "processing": "⏳ Thinking...",
    "menu": "🍴 **Main Menu**",
    "choose_language": "🌐 **Choose Language:**",
    "btn_favorites": "⭐️ Favorites",
    "btn_restart": "🔄 Restart",
    "btn_change_lang": "🌐 Language",
    "btn_help": "❓ Help",
    "btn_add_to_fav": "☆ Add to Favorites",
    "btn_remove_from_fav": "🌟 In Favorites",
    "btn_back": "⬅️ Back",
    "btn_another": "➡️ Another Recipe",
    "btn_buy_premium": "💎 Get Premium",
    "btn_page": "Page {page}/{total}",
    
    # --- Recipes ---
    "choose_category": "📝 **Select a category:**",
    "choose_dish": "🍳 **Select a dish:**",
    "recipe_title": "✨ **Recipe: {dish_name}**",
    "recipe_error": "❌ Error.",
    "dish_list_error": "❌ List Error.",
    "error_session_expired": "Session expired.",
    
    # --- Favorites ---
    "favorites_title": "⭐️ **Favorites**",
    "favorites_empty": "😔 Empty list.",
    "favorite_added": "⭐ Saved!",
    "favorite_removed": "🗑 Removed.",
    "favorite_limit": "❌ Limit reached.",
    
    # --- Paywalls & Errors ---
    "premium_required_title": "💎 Premium",
    "premium_required_text": "Feature locked.",
    "limit_favorites_exceeded": "🔒 Limit reached!",
    "welcome_gift_alert": "🎁 Gift soon!",
    "limit_voice_exceeded": "❌ Voice limit!",
    "limit_text_exceeded": "❌ Text limit!",
    "error_not_enough_products": "🤔 Need more ingredients.",
    "voice_recognized": "✅ Recognized: {text}",
    "error_generation": "❌ Error.",
    
    # --- Languages ---
    "lang_ru": "🇷🇺 Russian", 
    "lang_en": "🇬🇧 English", 
    "lang_de": "🇩🇪 German",
    "lang_fr": "🇫🇷 French", 
    "lang_it": "🇮🇹 Italian", 
    "lang_es": "🇪🇸 Spanish",
    "lang_changed": "🌐 Changed."
}

# Словарь TEXTS (Начальное заполнение)
TEXTS: Dict[str, Dict[str, str]] = {
    "en": BASE_EN.copy(),
    # Добавляем специфичные ключи для EN
    "en": {**BASE_EN, "premium_description": PREMIUM_DESC_EN}, 
    
    # Заглушки, которые мы заполним программно
    "de": {"premium_description": PREMIUM_DESC_DE}, 
    "fr": {"premium_description": PREMIUM_DESC_FR},
    "it": {"premium_description": PREMIUM_DESC_IT},
    "es": {"premium_description": PREMIUM_DESC_ES},
    "ru": {} # Руccкого нет в supported, но пусть будет чтобы не падал
}

# --- КРИТИЧЕСКИЙ ФИКС: ЗАПОЛНЕНИЕ ПУСТОТ ---
for lang in ["de", "fr", "it", "es", "ru"]:
    # 1. Если языка нет вообще - создаем
    if lang not in TEXTS: TEXTS[lang] = {}
    
    # 2. Идем по всем ключам Английского
    for key, value in BASE_EN.items():
        # Если в целевом языке ключа нет -> копируем из Английского
        if key not in TEXTS[lang]:
            TEXTS[lang][key] = value

def get_text(lang: str, key: str, **kwargs) -> str:
    # Защита от несуществующего языка
    if lang not in TEXTS: lang = "en"
    
    lang_dict = TEXTS[lang]
    # Защита от отсутствующего ключа (берем из EN)
    text = lang_dict.get(key, TEXTS["en"].get(key, "MISSING_TEXT"))
    
    if kwargs and text:
        try: return text.format(**kwargs)
        except: return text
    return text