# Полный texts.py, с реальным переводом "Welcome" для основных языков
# чтобы вы могли проверить переключение при старте.

from typing import Dict, Any, List
import logging
logger = logging.getLogger(__name__)

# --- Описания Премиума (сократил для примера, верните ваши полные версии) ---
P_EN = "Premium Features..."

# БАЗОВЫЙ АНГЛИЙСКИЙ
EN_BASE = {
    "lang_ru": "🇷🇺 Russian", "lang_en": "🇬🇧 English", "lang_de": "🇩🇪 Deutsch",
    "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español",
    "welcome": """👋 **Welcome to FoodWizard.pro!**\n🥕 **Have ingredients?** Dictate or write list.\n⚡️ **Or say:** "Give me a recipe for..." """,
    "welcome_gift_alert": "🎁 **Gift!** 7 Days Premium coming in 48h.",
    "menu": "🍴 **Main Menu**",
    # ... остальные кнопки ...
    "btn_favorites": "⭐️ Favorites", "btn_restart": "🔄 Restart", "btn_change_lang": "🌐 Language",
    "btn_help": "❓ Help", "btn_back": "⬅️ Back", "btn_buy_premium": "💎 Premium",
    "premium_description": P_EN
}

TEXTS: Dict[str, Dict[str, str]] = {
    "en": EN_BASE,
    
    # Немецкий
    "de": {
        "welcome": """👋 **Willkommen bei FoodWizard.pro!**\n🥕 **Haben Sie Zutaten?** Schreiben oder diktieren Sie.\n⚡️ **Oder:** "Rezept für..." """,
        "welcome_gift_alert": "🎁 **Geschenk!** 7 Tage Premium in 48 Stunden.",
        "menu": "🍴 **Hauptmenü**",
        "btn_favorites": "⭐️ Favoriten", "btn_help": "❓ Hilfe", "btn_back": "⬅️ Zurück"
    },
    
    # Французский
    "fr": {
        "welcome": """👋 **Bienvenue sur FoodWizard.pro!**\n🥕 **Ingrédients?** Écrivez ou dictez.\n⚡️ **Ou:** "Recette de..." """,
        "welcome_gift_alert": "🎁 **Cadeau !** 7 jours Premium dans 48h.",
        "menu": "🍴 **Menu Principal**",
        "btn_favorites": "⭐️ Favoris", "btn_help": "❓ Aide", "btn_back": "⬅️ Retour"
    },

    # Итальянский
    "it": {
        "welcome": """👋 **Benvenuto su FoodWizard.pro!**\n🥕 **Ingredienti?** Scrivili o dettali.\n⚡️ **O:** "Ricetta per..." """,
        "welcome_gift_alert": "🎁 **Regalo!** 7 giorni Premium tra 48 ore.",
        "menu": "🍴 **Menu Principale**",
        "btn_favorites": "⭐️ Preferiti", "btn_help": "❓ Aiuto", "btn_back": "⬅️ Indietro"
    },

    # Испанский
    "es": {
        "welcome": """👋 **¡Bienvenido a FoodWizard.pro!**\n🥕 **¿Ingredientes?** Escribe o dicta.\n⚡️ **O:** "Receta de..." """,
        "welcome_gift_alert": "🎁 **¡Regalo!** 7 días Premium en 48h.",
        "menu": "🍴 **Menú Principal**",
        "btn_favorites": "⭐️ Favoritos", "btn_help": "❓ Ayuda", "btn_back": "⬅️ Atrás"
    }
}

# Копируем английский для пропущенных ключей (fall back)
base = TEXTS["en"]
for lang in ["de", "fr", "it", "es"]:
    for k, v in base.items():
        if k not in TEXTS[lang]:
            TEXTS[lang][k] = v

def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in TEXTS: lang = "en"
    text = TEXTS[lang].get(key, TEXTS["en"].get(key, ""))
    if kwargs and text:
        try: return text.format(**kwargs)
        except: return text
    return text