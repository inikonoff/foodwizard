from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# --- ОПИСАНИЯ ПРЕМИУМА (Чтобы не загромождать основной словарь) ---
PREMIUM_DESC_EN = """💎 **Premium Benefits:**\n✅ **Favorites:** Unlimited saving\n✅ **Health:** Nutrition facts\n✅ **Limits:** 100 text / 50 voice\n👇 **Choose a plan:**"""
PREMIUM_DESC_DE = """💎 **Premium-Vorteile:**\n✅ **Favoriten:** Unbegrenzt\n✅ **Gesundheit:** Nährwerte\n✅ **Limits:** 100 Text / 50 Sprache\n👇 **Wählen Sie einen Plan:**"""
PREMIUM_DESC_FR = """💎 **Avantages Premium:**\n✅ **Favoris:** Illimité\n✅ **Santé:** Infos nutritionnelles\n✅ **Limites:** 100 texte / 50 voix\n👇 **Choisissez un plan:**"""
PREMIUM_DESC_IT = """💎 **Vantaggi Premium:**\n✅ **Preferiti:** Illimitati\n✅ **Salute:** Valori nutrizionali\n✅ **Limiti:** 100 testo / 50 vocale\n👇 **Scegli un piano:**"""
PREMIUM_DESC_ES = """💎 **Beneficios Premium:**\n✅ **Favoritos:** Ilimitado\n✅ **Salud:** Información nutricional\n✅ **Límites:** 100 texto / 50 voz\n👇 **Elige un plan:**"""

# ================= БАЗОВЫЙ АНГЛИЙСКИЙ (ИСТОЧНИК) =================
# Здесь ДОЛЖНЫ быть ВСЕ ключи, которые используются в коде
BASE_EN = {
    # --- Categories (Fixing "Missing") ---
    "soup": "🍜 Soups", 
    "main": "🥩 Main Courses", 
    "salad": "🥗 Salads", 
    "breakfast": "🥞 Breakfasts", 
    "dessert": "🍰 Desserts", 
    "drink": "🍹 Drinks", 
    "snack": "🥨 Snacks",
    
    # --- UI & Buttons ---
    "welcome": """👋 **Welcome to FoodWizard.pro!**\n🥕 **Have ingredients?**\nDictate or write them.\n⚡️ **Or say:**\n"Give me a recipe for [dish]" """,
    "processing": "⏳ Thinking...",  # <--- Fix для "Missing" при загрузке
    "menu": "🍴 **Main Menu**",
    "start_manual": "", 
    
    "btn_favorites": "⭐️ Favorites",
    "btn_restart": "🔄 Restart",
    "btn_change_lang": "🌐 Language",
    "btn_help": "❓ Help",
    "btn_back": "⬅️ Back",
    "btn_another": "➡️ Another Recipe",
    "btn_buy_premium": "💎 Get Premium",
    "btn_add_to_fav": "☆ Add to Favorites",
    "btn_remove_from_fav": "🌟 In Favorites",
    
    # --- Messages ---
    "choose_category": "📝 **Category:**",
    "choose_dish": "🍳 **Dish:**",
    "recipe_title": "✨ **Recipe: {dish_name}**",
    
    # --- Favorites ---
    "favorites_title": "⭐️ **Your Favorites**",
    "favorites_empty": "😔 List is empty.",
    "favorite_added": "⭐ Saved!",
    "favorite_removed": "🗑 Removed.",
    "limit_favorites_exceeded": "🔒 **Limit Reached!**\nGet Premium.",
    
    # --- Errors & Promos ---
    "error_not_enough_products": "🤔 Need more ingredients.",
    "error_generation": "❌ Error.",
    "error_session_expired": "Session expired.",
    "error_voice_recognition": "🗣️ Voice Error.",
    "voice_recognized": "✅ Recognized: {text}",
    "welcome_gift_alert": "🎁 **Gift!** 7 Days Premium coming in 48h.",
    "trial_activated_notification": "🎁 **Gift Active!** 7 Days Premium.",
    "promo_instruction": "ℹ️ Use: <code>/code CODE</code>",
    
    # --- Lang Names ---
    "lang_ru": "🇷🇺 Russian", "lang_en": "🇬🇧 English", "lang_de": "🇩🇪 Deutsch",
    "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español",
    "choose_language": "🌐 **Choose Language:**",
    "lang_changed": "🌐 Language changed.",
    
    # --- Fallbacks for keys that might be missing in logic ---
    "recipe_error": "❌ Error", "dish_list_error": "❌ Error",
    "premium_required_title": "💎 Premium", "premium_required_text": "Locked",
    "limit_voice_exceeded": "Limit", "limit_text_exceeded": "Limit",
    "safety_refusal": "No", "help_title": "Help", "help_text": "...", 
    "premium_description": PREMIUM_DESC_EN, "thanks": "ok", "easter_egg": "ok"
}

TEXTS: Dict[str, Dict[str, str]] = {
    # 1. EN
    "en": BASE_EN,
    
    # 2. DE (German) - Реальные переводы
    "de": {
        "welcome": """👋 **Willkommen!**\n🥕 **Zutaten?**\nSchreiben oder sprechen.\n⚡️ **Oder:**\n"Rezept für [Gericht]" """,
        "processing": "⏳ Moment...", 
        "menu": "🍴 **Menü**",
        "soup": "🍜 Suppen", "main": "🥩 Hauptgerichte", "salad": "🥗 Salate", 
        "breakfast": "🥞 Frühstücke", "dessert": "🍰 Desserts", "drink": "🍹 Getränke", "snack": "🥨 Snacks",
        "btn_favorites": "⭐️ Favoriten", "btn_help": "❓ Hilfe", "btn_back": "⬅️ Zurück",
        "btn_add_to_fav": "☆ Speichern", "btn_remove_from_fav": "🌟 Gespeichert",
        "favorites_title": "⭐️ **Favoriten**", "favorites_empty": "😔 Leer.",
        "lang_changed": "🌐 Deutsch",
        "premium_description": PREMIUM_DESC_DE
    },

    # 3. FR (French)
    "fr": {
        "welcome": """👋 **Bienvenue !**\n🥕 **Ingrédients ?**\nÉcrivez ou dictez.\n⚡️ **Ou :**\n"Recette de [plat]" """,
        "processing": "⏳ Attente...",
        "menu": "🍴 **Menu**",
        "soup": "🍜 Soupes", "main": "🥩 Plats", "salad": "🥗 Salades", 
        "breakfast": "🥞 Petit-déj", "dessert": "🍰 Desserts", "drink": "🍹 Boissons", "snack": "🥨 Snacks",
        "btn_favorites": "⭐️ Favoris", "btn_help": "❓ Aide", "btn_back": "⬅️ Retour",
        "btn_add_to_fav": "☆ Sauvegarder", "btn_remove_from_fav": "🌟 Enregistré",
        "favorites_title": "⭐️ **Favoris**", "favorites_empty": "😔 Vide.",
        "lang_changed": "🌐 Français",
        "premium_description": PREMIUM_DESC_FR
    },
    
    # 4. IT (Italian)
    "it": {
        "welcome": """👋 **Benvenuto!**\n🥕 **Ingredienti?**\nScrivi o detta.\n⚡️ **O:**\n"Ricetta per [piatto]" """,
        "processing": "⏳ Attendo...",
        "menu": "🍴 **Menu**",
        "soup": "🍜 Zuppe", "main": "🥩 Secondi", "salad": "🥗 Insalate", 
        "breakfast": "🥞 Colazione", "dessert": "🍰 Dessert", "drink": "🍹 Bevande", "snack": "🥨 Snack",
        "btn_favorites": "⭐️ Preferiti", "btn_help": "❓ Aiuto", "btn_back": "⬅️ Indietro",
        "btn_add_to_fav": "☆ Salva", "btn_remove_from_fav": "🌟 Salvato",
        "favorites_title": "⭐️ **Preferiti**", "favorites_empty": "😔 Vuota.",
        "lang_changed": "🌐 Italiano",
        "premium_description": PREMIUM_DESC_IT
    },

    # 5. ES (Spanish)
    "es": {
        "welcome": """👋 **¡Hola!**\n🥕 **¿Ingredientes?**\nEscribe o dicta.\n⚡️ **O:**\n"Receta de [plato]" """,
        "processing": "⏳ Pensando...",
        "menu": "🍴 **Menú**",
        "soup": "🍜 Sopas", "main": "🥩 Platos", "salad": "🥗 Ensaladas", 
        "breakfast": "🥞 Desayuno", "dessert": "🍰 Postres", "drink": "🍹 Bebidas", "snack": "🥨 Snacks",
        "btn_favorites": "⭐️ Favoritos", "btn_help": "❓ Ayuda", "btn_back": "⬅️ Atrás",
        "btn_add_to_fav": "☆ Guardar", "btn_remove_from_fav": "🌟 Guardado",
        "favorites_title": "⭐️ **Favoritos**", "favorites_empty": "😔 Vacío.",
        "lang_changed": "🌐 Español",
        "premium_description": PREMIUM_DESC_ES
    }
}

# --- СКРИПТ АВТОЗАПОЛНЕНИЯ (Важен для безопасности) ---
# Если мы забыли перевести какой-то ключ (например, кнопку рестарта), 
# скрипт подставит английскую версию, чтобы не было ошибки None.
for lang in ["de", "fr", "it", "es"]:
    for key, value in BASE_EN.items():
        if key not in TEXTS[lang]:
            TEXTS[lang][key] = value

def get_text(lang: str, key: str, **kwargs) -> str:
    # 1. Защита языка
    if lang not in TEXTS: lang = "en"
    
    # 2. Поиск текста
    lang_dict = TEXTS[lang]
    # Фолбэк: Родной -> Английский -> Ключ (с заглавной буквы)
    text = lang_dict.get(key, TEXTS["en"].get(key, str(key).capitalize())) 
    
    # Если вернулся "MISSING" (по старой памяти) - возвращаем ключ
    if text == "MISSING":
        text = str(key).capitalize()
    
    if kwargs and text:
        try: return text.format(**kwargs)
        except: return text
    return text