from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# --- Описания Премиума (Оставьте ваши версии) ---
# ... (Код сокращен, используйте то, что уже было) ...
PREMIUM_DESC_EN = """💎 **Premium Benefits:**\n\n✅ **Favorites:** Unlimited saving\n✅ **Health:** Nutrition facts\n✅ **Limits:** 100 text / 50 voice\n👇 **Choose a plan:**"""
PREMIUM_DESC_DE = "💎 Premium-Vorteile:..." # (ваши тексты)
PREMIUM_DESC_FR = "💎 Avantages Premium :..."
PREMIUM_DESC_IT = "💎 Vantaggi Premium:..."
PREMIUM_DESC_ES = "💎 Beneficios Premium:..."

# ЭТАЛОН (EN)
BASE_EN = {
    # Ключи, которые возвращает Groq (ТЕПЕРЬ СТРОГО EN)
    "soup": "🍜 Soups", 
    "main": "🥩 Main Courses", 
    "salad": "🥗 Salads", 
    "breakfast": "🥞 Breakfasts", 
    "dessert": "🍰 Desserts", 
    "drink": "🍹 Drinks", 
    "snack": "🥨 Snacks",
    
    # UI
    "welcome": """👋 **Welcome to FoodWizard.pro!**\n🥕 **Ingredients?**\nDictate or write them.\n⚡️ **Or say:**\n"Give me a recipe for [dish]\"""",
    "menu": "🍴 **Main Menu**", "processing": "⏳ Thinking...", "start_manual": "",

    # КНОПКИ
    "btn_favorites": "⭐️ Favorites", "btn_restart": "🔄 Restart", "btn_change_lang": "🌐 Language", 
    "btn_help": "❓ Help", "btn_back": "⬅️ Back", "btn_buy_premium": "💎 Get Premium",
    "btn_add_to_fav": "☆ Add to Favorites", "btn_remove_from_fav": "🌟 In Favorites", "btn_another": "➡️ Another Recipe",
    "btn_page": "Page {page}/{total}",

    # TEKST
    "choose_category": "📝 **Category:**", "choose_dish": "🍳 **Dish:**", "recipe_title": "✨ {dish_name}", 
    "favorites_title": "⭐️ **Favorites**", "favorites_empty": "😔 List is empty.",
    "premium_required_title": "💎 Premium", "premium_required_text": "Locked.", "premium_description": PREMIUM_DESC_EN,
    "limit_favorites_exceeded": "🔒 Limit 3.", "welcome_gift_alert": "🎁 Gift in 48h.", "trial_activated_notification": "🎁 Gift active.",
    "limit_voice_exceeded": "❌ Voice limit!", "limit_text_exceeded": "❌ Text limit!",
    "error_voice_recognition": "🗣️ Error.", "error_generation": "❌ Error.", "error_not_enough_products": "🤔 Need ingredients.",
    "voice_recognized": "✅ Recognized: {text}", "lang_changed": "🌐 Changed.",
    "help_title": "❓ **Help**", "help_text": "Send ingredients.", "promo_instruction": "ℹ️ Code: /code ...",
    "lang_ru": "🇷🇺 Russian", "lang_en": "🇬🇧 English", "lang_de": "🇩🇪 Deutsch", 
    "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español"
}

TEXTS: Dict[str, Dict[str, str]] = {
    "en": BASE_EN,
    
    "de": { # НЕМЕЦКИЙ (Полный словарь, чтобы не было пропусков)
        "soup": "🍜 Suppen", "main": "🥩 Hauptgerichte", "salad": "🥗 Salate", 
        "breakfast": "🥞 Frühstücke", "dessert": "🍰 Desserts", "drink": "🍹 Getränke", "snack": "🥨 Snacks",
        "btn_favorites": "⭐️ Favoriten", "btn_restart": "🔄 Neustart", "btn_change_lang": "🌐 Sprache", "btn_help": "❓ Hilfe",
        "btn_add_to_fav": "☆ Speichern", "btn_remove_from_fav": "🌟 Gespeichert", "btn_back": "⬅️ Zurück", "btn_another": "➡️ Weiter",
        "premium_description": PREMIUM_DESC_DE,
        "menu": "🍴 **Menü**", "processing": "⏳ Moment...", 
        # (добавьте сюда welcome, gift и другие переводы из прошлых версий, если они исчезли)
    },
    
    "fr": { # ФРАНЦУЗСКИЙ
        "soup": "🍜 Soupes", "main": "🥩 Plats", "salad": "🥗 Salades", 
        "breakfast": "🥞 Petit-déj", "dessert": "🍰 Desserts", "drink": "🍹 Boissons", "snack": "🥨 Snacks",
        "btn_favorites": "⭐️ Favoris", "btn_restart": "🔄 Redémarrer", "btn_change_lang": "🌐 Langue", "btn_help": "❓ Aide",
        "btn_add_to_fav": "☆ Sauvegarder", "btn_remove_from_fav": "🌟 Enregistré", "btn_back": "⬅️ Retour", "btn_another": "➡️ Autre",
        "premium_description": PREMIUM_DESC_FR,
        "menu": "🍴 **Menu**", "processing": "⏳ Attente...",
    },
    
    "it": { # ИТАЛЬЯНСКИЙ (Фикс для Zuppe и Secondi)
        "soup": "🍜 Zuppe", "main": "🥩 Secondi", "salad": "🥗 Insalate", 
        "breakfast": "🥞 Colazione", "dessert": "🍰 Dessert", "drink": "🍹 Bevande", "snack": "🥨 Snack",
        "btn_favorites": "⭐️ Preferiti", "btn_restart": "🔄 Riavvia", "btn_change_lang": "🌐 Lingua", "btn_help": "❓ Aiuto",
        "btn_add_to_fav": "☆ Salva", "btn_remove_from_fav": "🌟 Salvato", "btn_back": "⬅️ Indietro", "btn_another": "➡️ Altro",
        "premium_description": PREMIUM_DESC_IT,
        "menu": "🍴 **Menu**", "processing": "⏳ Attendo...",
    },
    
    "es": { # ИСПАНСКИЙ
        "soup": "🍜 Sopas", "main": "🥩 Platos", "salad": "🥗 Ensaladas", 
        "breakfast": "🥞 Desayuno", "dessert": "🍰 Postres", "drink": "🍹 Bebidas", "snack": "🥨 Snacks",
        "btn_favorites": "⭐️ Favoritos", "btn_restart": "🔄 Reiniciar", "btn_change_lang": "🌐 Idioma", "btn_help": "❓ Ayuda",
        "btn_add_to_fav": "☆ Guardar", "btn_remove_from_fav": "🌟 Guardado", "btn_back": "⬅️ Atrás", "btn_another": "➡️ Otro",
        "premium_description": PREMIUM_DESC_ES,
        "menu": "🍴 **Menú**", "processing": "⏳ Pensando...",
    }
}

# AUTO-FILL FROM EN
base = TEXTS["en"]
for lang in ["de", "fr", "it", "es"]:
    if lang not in TEXTS: TEXTS[lang] = {}
    for k, v in base.items():
        if k not in TEXTS[lang]: TEXTS[lang][k] = v

def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in TEXTS: lang = "en"
    text = TEXTS[lang].get(key, TEXTS["en"].get(key, ""))
    if kwargs and text:
        try: return text.format(**kwargs)
        except: return text
    return text