from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# --- ОПИСАНИЯ ПРЕМИУМА (Неизменны) ---
PREMIUM_DESC_EN = """💎 **Premium Benefits:**
✅ **Favorites:** Unlimited saving
✅ **Health:** Nutrition facts
✅ **Limits:** 100 text / 50 voice
✅ **Ingredients:** Up to 50
👇 **Choose a plan:**"""

PREMIUM_DESC_DE = """💎 **Premium-Vorteile:**
✅ **Favoriten:** Unbegrenzt
✅ **Gesundheit:** Nährwertangaben
✅ **Limits:** 100 Text / 50 Sprache
👇 **Plan wählen:**"""

PREMIUM_DESC_FR = """💎 **Avantages Premium :**
✅ **Favoris :** Illimité
✅ **Santé :** Infos nutritionnelles
✅ **Limites :** 100 texte / 50 voix
👇 **Choisissez un plan :**"""

PREMIUM_DESC_IT = """💎 **Vantaggi Premium:**
✅ **Preferiti:** Illimitati
✅ **Salute:** Valori nutrizionali
✅ **Limiti:** 100 testo / 50 vocale
✅ **Ingredienti:** Fino a 50
👇 **Scegli un piano:**"""

PREMIUM_DESC_ES = """💎 **Beneficios Premium:**
✅ **Favoritos:** Ilimitado
✅ **Salud:** Información nutricional
✅ **Límites:** 100 texto / 50 voz
👇 **Elige un plan:**"""


TEXTS: Dict[str, Dict[str, str]] = {
    
    # ================= ENGLISH (EN) =================
    "en": {
        "lang_ru": "🇷🇺 Russian", "lang_en": "🇬🇧 English", "lang_de": "🇩🇪 Deutsch",
        "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español",

        # UI
        "welcome": """👋 **Welcome to FoodWizard.pro!**\n🥕 **Ingredients?**\nDictate or write them.\n⚡️ **Or say:**\n"Give me a recipe for [dish]\"""",
        "menu": "🍴 **Main Menu**", "processing": "⏳ Thinking...", "start_manual": "",

        # КАТЕГОРИИ (КЛЮЧИ)
        "soup": "🍜 Soups", "main": "🥩 Main Courses", "salad": "🥗 Salads", 
        "breakfast": "🥞 Breakfasts", "dessert": "🍰 Desserts", "drink": "🍹 Drinks", "snack": "🥨 Snacks",
        
        # BUTTONS
        "btn_favorites": "⭐️ Favorites", "btn_restart": "🔄 Restart", "btn_change_lang": "🌐 Language", 
        "btn_help": "❓ Help", "btn_back": "⬅️ Back", "btn_buy_premium": "💎 Get Premium",
        "btn_add_to_fav": "☆ Add to Favorites", "btn_remove_from_fav": "🌟 In Favorites", "btn_another": "➡️ Another Recipe",
        "btn_page": "Page {page}/{total}",

        # MESSAGES
        "choose_category": "📝 **Category:**", "choose_dish": "🍳 **Dish:**",
        "favorites_title": "⭐️ **Favorites**", "favorites_empty": "😔 List is empty.",
        "limit_favorites_exceeded": "🔒 Limit reached (3). Get Premium.",
        "premium_required_title": "💎 Premium Required", "premium_required_text": "Favorites are locked.",
        "welcome_gift_alert": "🎁 **Gift!** 7 Days Premium coming in 48h.",
        "trial_activated_notification": "🎁 **Gift Active!** 7 Days Premium.",
        
        "limit_voice_exceeded": "❌ Voice limit!", "limit_text_exceeded": "❌ Text limit!",
        "error_voice_recognition": "🗣️ Voice Error.", "error_generation": "❌ Error.", "error_not_enough_products": "🤔 Need ingredients.",
        "voice_recognized": "✅ {text}", "lang_changed": "🌐 Language changed.",
        "help_title": "❓ Help", "help_text": "Send ingredients.",
        "promo_instruction": "ℹ️ Use: <code>/code CODE</code>",
        "premium_description": PREMIUM_DESC_EN,
        "bot_description": "...", "bot_short_description": "...", "thanks": "😊", "easter_egg": "🥚", "recipe_error": "❌ Error", "dish_list_error": "❌ Error", "error_session_expired": "Expired", "favorite_added": "Saved", "favorite_removed": "Removed", "favorite_limit": "Limit", "safety_refusal": "No"
    },

    # ================= GERMAN (DE) =================
    "de": {
        "welcome": """👋 **Willkommen!**\n🥕 **Zutaten?**\nSchreiben oder sprechen.\n⚡️ **Oder:**\n"Rezept für [Gericht]" """,
        # ПЕРЕВОД КАТЕГОРИЙ (ЯВНЫЙ)
        "soup": "🍜 Suppen", "main": "🥩 Hauptgerichte", "salad": "🥗 Salate", 
        "breakfast": "🥞 Frühstück", "dessert": "🍰 Desserts", "drink": "🍹 Getränke", "snack": "🥨 Snacks",
        
        "menu": "🍴 **Menü**", "processing": "⏳ Moment...",
        "btn_favorites": "⭐️ Favoriten", "btn_restart": "🔄 Neustart", "btn_change_lang": "🌐 Sprache", 
        "btn_help": "❓ Hilfe", "btn_back": "⬅️ Zurück", "btn_buy_premium": "💎 Premium",
        "btn_add_to_fav": "☆ Speichern", "btn_remove_from_fav": "🌟 Gespeichert", "btn_another": "➡️ Noch eins",
        "choose_category": "📝 **Kategorie:**", "choose_dish": "🍳 **Gericht:**",
        "favorites_title": "⭐️ **Favoriten**", "favorites_empty": "😔 Leer.",
        "premium_description": PREMIUM_DESC_DE,
        "lang_changed": "🌐 Deutsch",
        "promo_instruction": "ℹ️ Benutze: <code>/code CODE</code>"
    },

    # ================= FRENCH (FR) =================
    "fr": {
        "welcome": """👋 **Bienvenue !**\n🥕 **Ingrédients ?**\nÉcrivez ou dictez.\n⚡️ **Ou :**\n"Recette de [plat]" """,
        # ПЕРЕВОД КАТЕГОРИЙ
        "soup": "🍜 Soupes", "main": "🥩 Plats", "salad": "🥗 Salades", 
        "breakfast": "🥞 Petit-déj", "dessert": "🍰 Desserts", "drink": "🍹 Boissons", "snack": "🥨 Snacks",

        "menu": "🍴 **Menu**", "processing": "⏳ Attente...",
        "btn_favorites": "⭐️ Favoris", "btn_restart": "🔄 Redémarrer", "btn_change_lang": "🌐 Langue", 
        "btn_help": "❓ Aide", "btn_back": "⬅️ Retour", "btn_buy_premium": "💎 Premium",
        "btn_add_to_fav": "☆ Sauvegarder", "btn_remove_from_fav": "🌟 Enregistré", "btn_another": "➡️ Autre",
        "choose_category": "📝 **Catégorie :**", "choose_dish": "🍳 **Plat :**",
        "favorites_title": "⭐️ **Favoris**", "favorites_empty": "😔 Vide.",
        "premium_description": PREMIUM_DESC_FR,
        "lang_changed": "🌐 Français",
        "promo_instruction": "ℹ️ Utilisez : <code>/code CODE</code>"
    },

    # ================= ITALIAN (IT) - ВОТ ТУТ БЫЛО NONE =================
    "it": {
        "welcome": """👋 **Benvenuto!**\n🥕 **Ingredienti?**\nScrivi o detta.\n⚡️ **O:**\n"Ricetta per [piatto]" """,
        # ЯВНЫЙ ПЕРЕВОД КАТЕГОРИЙ (ФИКС ОШИБКИ NONE)
        "soup": "🍜 Zuppe", 
        "main": "🥩 Secondi", 
        "salad": "🥗 Insalate", 
        "breakfast": "🥞 Colazione", 
        "dessert": "🍰 Dessert", 
        "drink": "🍹 Bevande", 
        "snack": "🥨 Snack",

        "menu": "🍴 **Menu**", "processing": "⏳ Attendo...",
        "btn_favorites": "⭐️ Preferiti", "btn_restart": "🔄 Riavvia", "btn_change_lang": "🌐 Lingua", 
        "btn_help": "❓ Aiuto", "btn_back": "⬅️ Indietro", "btn_buy_premium": "💎 Premium",
        "btn_add_to_fav": "☆ Salva", "btn_remove_from_fav": "🌟 Salvato", "btn_another": "➡️ Altro",
        "choose_category": "📝 **Categoria:**", "choose_dish": "🍳 **Piatto:**",
        "favorites_title": "⭐️ **Preferiti**", "favorites_empty": "😔 Vuota.",
        "premium_description": PREMIUM_DESC_IT,
        "lang_changed": "🌐 Italiano",
        "promo_instruction": "ℹ️ Usa: <code>/code CODE</code>"
    },

    # ================= SPANISH (ES) =================
    "es": {
        "welcome": """👋 **¡Hola!**\n🥕 **¿Ingredientes?**\nEscribe o dicta.\n⚡️ **O:**\n"Receta de [plato]" """,
        # ПЕРЕВОД КАТЕГОРИЙ
        "soup": "🍜 Sopas", "main": "🥩 Platos", "salad": "🥗 Ensaladas", 
        "breakfast": "🥞 Desayuno", "dessert": "🍰 Postres", "drink": "🍹 Bebidas", "snack": "🥨 Snacks",

        "menu": "🍴 **Menú**", "processing": "⏳ Pensando...",
        "btn_favorites": "⭐️ Favoritos", "btn_restart": "🔄 Reiniciar", "btn_change_lang": "🌐 Idioma", 
        "btn_help": "❓ Ayuda", "btn_back": "⬅️ Atrás", "btn_buy_premium": "💎 Premium",
        "btn_add_to_fav": "☆ Guardar", "btn_remove_from_fav": "🌟 Guardado", "btn_another": "➡️ Otro",
        "choose_category": "📝 **Categoría:**", "choose_dish": "🍳 **Plato:**",
        "favorites_title": "⭐️ **Favoritos**", "favorites_empty": "😔 Vacío.",
        "premium_description": PREMIUM_DESC_ES,
        "lang_changed": "🌐 Español",
        "promo_instruction": "ℹ️ Usa: <code>/code CODE</code>"
    }
}

# --- ЗАПОЛНЕНИЕ ОСТАВШИХСЯ ПРОБЕЛОВ (БЕЗОПАСНОСТЬ) ---
base_lang = TEXTS["en"]
# Копируем список языков (названия) и всё остальное, что забыли, из EN
for lang in ["de", "fr", "it", "es"]:
    for key, val in base_lang.items():
        if key not in TEXTS[lang]:
            TEXTS[lang][key] = val

def get_text(lang: str, key: str, **kwargs) -> str:
    # 1. Защита языка (Fallback to EN)
    if lang not in TEXTS: lang = "en"
    
    lang_dict = TEXTS[lang]
    # 2. Защита ключа (Fallback to EN text -> Fallback to KEY itself)
    # Если перевода нет ни в целевом, ни в английском, вернет название ключа (напр "soup")
    text = lang_dict.get(key, TEXTS["en"].get(key, str(key).capitalize())) 
    
    if kwargs and text:
        try: return text.format(**kwargs)
        except KeyError: return text
    return text