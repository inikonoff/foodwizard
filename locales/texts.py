from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# --- ШАБЛОНЫ ПРЕМИУМА ---
PREMIUM_DESC_EN = """💎 **Premium Benefits:**\n\n✅ **Favorites:** Unlimited saving\n✅ **Health:** Nutrition facts\n✅ **Limits:** 100 text / 50 voice\n✅ **Ingredients:** 50 items/request\n👇 **Choose a plan:**"""
PREMIUM_DESC_DE = """💎 **Premium-Vorteile:**\n\n✅ **Favoriten:** Unbegrenzt speichern\n✅ **Gesundheit:** Nährwertangaben\n✅ **Limits:** 100 Text / 50 Sprache\n👇 **Wählen Sie einen Plan:**"""
PREMIUM_DESC_FR = """💎 **Avantages Premium :**\n\n✅ **Favoris :** Illimité\n✅ **Santé :** Infos nutritionnelles\n✅ **Limites :** 100 texte / 50 voix\n👇 **Choisissez un plan :**"""
PREMIUM_DESC_IT = """💎 **Vantaggi Premium:**\n\n✅ **Preferiti:** Illimitati\n✅ **Salute:** Valori nutrizionali\n✅ **Limiti:** 100 testo / 50 vocale\n👇 **Scegli un piano:**"""
PREMIUM_DESC_ES = """💎 **Beneficios Premium:**\n\n✅ **Favoritos:** Ilimitado\n✅ **Salud:** Información nutricional\n✅ **Límites:** 100 texto / 50 voz\n👇 **Elige un plan:**"""

# ================= БАЗОВЫЙ АНГЛИЙСКИЙ =================
BASE_EN = {
    # UI Essentials
    "menu": "🍴 **Main Menu**",
    "processing": "⏳ Thinking...",
    "start_manual": "", 
    
    # КНОПКИ КАТЕГОРИЙ (ВКЛЮЧАЯ PLURAL ЗАЩИТУ)
    "soup": "🍜 Soups",      "soups": "🍜 Soups",
    "main": "🥩 Main Dish",  "mains": "🥩 Main Dish", "main dish": "🥩 Main Dish",
    "salad": "🥗 Salads",    "salads": "🥗 Salads",
    "breakfast": "🥞 Breakfast", "breakfasts": "🥞 Breakfast",
    "dessert": "🍰 Dessert", "desserts": "🍰 Desserts",
    "drink": "🍹 Drinks",    "drinks": "🍹 Drinks",
    "snack": "🥨 Snacks",    "snacks": "🥨 Snacks",
    
    # ТЕКСТЫ
    "welcome": """👋 **Welcome to FoodWizard.pro!**\n\n🥕 **Ingredients?**\nDictate or write a list.\n⚡️ **Or say:**\n"Give me a recipe for [dish]\"""",
    
    "choose_category": "📝 **Category:**", 
    "choose_dish": "🍳 **Dish:**",
    
    # КНОПКИ
    "btn_favorites": "⭐️ Favorites", "btn_restart": "🔄 Restart", "btn_change_lang": "🌐 Language", 
    "btn_help": "❓ Help", "btn_back": "⬅️ Back", "btn_buy_premium": "💎 Get Premium",
    "btn_add_to_fav": "☆ Add", "btn_remove_from_fav": "🌟 Saved", "btn_another": "➡️ More",
    "btn_page": "Page {page}/{total}",
    
    # СТАТУСЫ И ОШИБКИ
    "recipe_title": "✨ {dish_name}", "recipe_error": "❌ Error",
    "favorites_title": "⭐️ **Favorites**", "favorites_empty": "😔 List is empty.",
    "favorite_added": "⭐ Saved!", "favorite_removed": "🗑 Removed.",
    "premium_required_title": "💎 Premium", "premium_required_text": "Feature locked.",
    "premium_description": PREMIUM_DESC_EN,
    "limit_favorites_exceeded": "🔒 Limit 3.", 
    "limit_voice_exceeded": "❌ Voice limit!", "limit_text_exceeded": "❌ Text limit!",
    "error_voice_recognition": "🗣️ Voice Error.", "error_generation": "❌ Error.",
    "error_not_enough_products": "🤔 Need more ingredients.",
    "voice_recognized": "✅ Recognized: {text}", "lang_changed": "🌐 Changed.",
    "safety_refusal": "🚫 Food only.", "promo_instruction": "ℹ️ Code: /code ...",
    "welcome_gift_alert": "🎁 **Gift!** 7 Days Premium coming in 48h.",
    "trial_activated_notification": "🎁 **Gift Active!** 7 Days Premium.",
    "help_title": "Help", "help_text": "Send ingredients.",
    
    # ЯЗЫКИ
    "lang_ru": "🇷🇺 Russian", "lang_en": "🇬🇧 English", "lang_de": "🇩🇪 Deutsch", 
    "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español"
}

TEXTS: Dict[str, Dict[str, str]] = {
    # 1. EN
    "en": BASE_EN,

    # 2. DE (GERMAN) - ПРОВЕРЕННЫЕ КАТЕГОРИИ
    "de": {
        "soup": "🍜 Suppen",     "soups": "🍜 Suppen",
        "main": "🥩 Hauptspeise", "mains": "🥩 Hauptspeisen",
        "salad": "🥗 Salate",    "salads": "🥗 Salate",
        "breakfast": "🥞 Frühstück", 
        "dessert": "🍰 Desserts", "desserts": "🍰 Desserts",
        "drink": "🍹 Getränke",  "drinks": "🍹 Getränke",
        "snack": "🥨 Snacks",    "snacks": "🥨 Snacks",
        
        "welcome": """👋 **Willkommen!**\n🥕 **Zutaten?**\nSchreiben oder sprechen.\n⚡️ **Oder:** "Rezept für..." """,
        "btn_favorites": "⭐️ Favoriten", "btn_restart": "🔄 Neustart", "btn_change_lang": "🌐 Sprache", 
        "btn_help": "❓ Hilfe", "btn_back": "⬅️ Zurück", "btn_buy_premium": "💎 Premium",
        "btn_add_to_fav": "☆ Speichern", "btn_remove_from_fav": "🌟 Gespeichert", "btn_another": "➡️ Weiter",
        "favorites_title": "⭐️ **Favoriten**", "favorites_empty": "😔 Leer.",
        "lang_changed": "🌐 Deutsch",
        "premium_description": PREMIUM_DESC_DE,
        "processing": "⏳ Moment...",
        "choose_category": "📝 **Kategorie:**", "choose_dish": "🍳 **Gericht:**",
    },

    # 3. FR (FRENCH)
    "fr": {
        "soup": "🍜 Soupes",     "soups": "🍜 Soupes",
        "main": "🥩 Plats",      "mains": "🥩 Plats",
        "salad": "🥗 Salades",   "salads": "🥗 Salades",
        "breakfast": "🥞 Petit-déj",
        "dessert": "🍰 Desserts", "desserts": "🍰 Desserts",
        "drink": "🍹 Boissons",  "drinks": "🍹 Boissons",
        "snack": "🥨 Snacks",    "snacks": "🥨 Snacks",
        
        "welcome": """👋 **Bienvenue !**\n🥕 **Ingrédients ?**\nÉcrivez ou dictez.\n⚡️ **Ou :** "Recette de..." """,
        "btn_favorites": "⭐️ Favoris", "btn_restart": "🔄 Redémarrer", "btn_change_lang": "🌐 Langue",
        "btn_help": "❓ Aide", "btn_back": "⬅️ Retour", "btn_buy_premium": "💎 Premium",
        "btn_add_to_fav": "☆ Sauvegarder", "btn_remove_from_fav": "🌟 Enregistré", "btn_another": "➡️ Autre",
        "favorites_title": "⭐️ **Favoris**", "favorites_empty": "😔 Vide.",
        "lang_changed": "🌐 Français",
        "premium_description": PREMIUM_DESC_FR,
        "processing": "⏳ Attente...",
        "choose_category": "📝 **Catégorie :**", "choose_dish": "🍳 **Plat :**",
    },

    # 4. IT (ITALIAN) - ИСПРАВЛЕНЫ "None"
    "it": {
        "soup": "🍜 Zuppe",       "soups": "🍜 Zuppe",
        "main": "🥩 Secondi",     "mains": "🥩 Secondi",
        "salad": "🥗 Insalate",   "salads": "🥗 Insalate",
        "breakfast": "🥞 Colazione", 
        "dessert": "🍰 Dessert",  "desserts": "🍰 Dessert",
        "drink": "🍹 Bevande",    "drinks": "🍹 Bevande",
        "snack": "🥨 Snack",      "snacks": "🥨 Snack",
        
        "welcome": """👋 **Benvenuto!**\n🥕 **Ingredienti?**\nScrivi o detta.\n⚡️ **O:** "Ricetta per..." """,
        "btn_favorites": "⭐️ Preferiti", "btn_restart": "🔄 Riavvia", "btn_change_lang": "🌐 Lingua",
        "btn_help": "❓ Aiuto", "btn_back": "⬅️ Indietro", "btn_buy_premium": "💎 Premium",
        "btn_add_to_fav": "☆ Salva", "btn_remove_from_fav": "🌟 Salvato", "btn_another": "➡️ Altro",
        "favorites_title": "⭐️ **Preferiti**", "favorites_empty": "😔 Vuota.",
        "lang_changed": "🌐 Italiano",
        "premium_description": PREMIUM_DESC_IT,
        "processing": "⏳ Attendo...",
        "choose_category": "📝 **Categoria:**", "choose_dish": "🍳 **Piatto:**",
    },

    # 5. ES (SPANISH)
    "es": {
        "soup": "🍜 Sopas",       "soups": "🍜 Sopas",
        "main": "🥩 Platos",      "mains": "🥩 Platos",
        "salad": "🥗 Ensaladas",  "salads": "🥗 Ensaladas",
        "breakfast": "🥞 Desayuno", 
        "dessert": "🍰 Postres",  "desserts": "🍰 Postres",
        "drink": "🍹 Bebidas",    "drinks": "🍹 Bebidas",
        "snack": "🥨 Snacks",     "snacks": "🥨 Snacks",
        
        "welcome": """👋 **¡Hola!**\n🥕 **¿Ingredientes?**\nEscribe o dicta.\n⚡️ **O:** "Receta de..." """,
        "btn_favorites": "⭐️ Favoritos", "btn_restart": "🔄 Reiniciar", "btn_change_lang": "🌐 Idioma",
        "btn_help": "❓ Ayuda", "btn_back": "⬅️ Atrás", "btn_buy_premium": "💎 Premium",
        "btn_add_to_fav": "☆ Guardar", "btn_remove_from_fav": "🌟 Guardado", "btn_another": "➡️ Otro",
        "favorites_title": "⭐️ **Favoritos**", "favorites_empty": "😔 Vacío.",
        "lang_changed": "🌐 Español",
        "premium_description": PREMIUM_DESC_ES,
        "processing": "⏳ Pensando...",
        "choose_category": "📝 **Categoría:**", "choose_dish": "🍳 **Plato:**",
    }
}

# 1. ЗАПОЛНЕНИЕ ПУСТОТ ИЗ EN (БЕЗОПАСНОСТЬ)
base = TEXTS["en"]
for lang in ["de", "fr", "it", "es"]:
    if lang not in TEXTS: TEXTS[lang] = {}
    for k, v in base.items():
        if k not in TEXTS[lang]:
            TEXTS[lang][k] = v

def get_text(lang: str, key: str, **kwargs) -> str:
    # Если языка нет (напр. китайский), даем EN
    if lang not in TEXTS: lang = "en"
    
    # Берем словарь языка
    lang_dict = TEXTS[lang]
    
    # Пытаемся найти ключ. 
    # Если его нет в целевом языке - берем из EN.
    # Если и там нет - возвращаем ключ с большой буквы (чтобы на кнопке хоть что-то было).
    fallback_value = TEXTS["en"].get(key, str(key).title())
    text = lang_dict.get(key, fallback_value)
    
    if kwargs and text:
        try: return text.format(**kwargs)
        except: return text
    return text