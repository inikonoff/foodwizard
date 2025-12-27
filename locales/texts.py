from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

PREMIUM_DESC_EN = """💎 **Premium Benefits:**
✅ **Favorites:** Unlimited saving
✅ **Health:** Nutrition facts (Calories/Macros)
✅ **Limits:** 100 text / 50 voice (daily)
✅ **Ingredients:** Up to 50 per request
👇 **Choose a plan:**"""

PREMIUM_DESC_DE = """💎 **Premium-Vorteile:**
✅ **Favoriten:** Unbegrenzt speichern
✅ **Gesundheit:** Nährwertangaben (Kalorien)
✅ **Limits:** 100 Text / 50 Sprache
👇 **Wählen Sie einen Plan:**"""

PREMIUM_DESC_FR = """💎 **Avantages Premium :**
✅ **Favoris :** Sauvegarde illimitée
✅ **Santé :** Infos nutritionnelles
✅ **Limites :** 100 texte / 50 voix
👇 **Choisissez un plan :**"""

PREMIUM_DESC_IT = """💎 **Vantaggi Premium:**
✅ **Preferiti:** Illimitati
✅ **Salute:** Valori nutrizionali
✅ **Limiti:** 100 testo / 50 vocale
👇 **Scegli un piano:**"""

PREMIUM_DESC_ES = """💎 **Beneficios Premium:**
✅ **Favoritos:** Ilimitados
✅ **Salud:** Información nutricional
✅ **Límites:** 100 texto / 50 voz
👇 **Elige un plan:**"""

# Добавьте эти строки в TEXTS["en"] (после "promo_instruction"):
TEXTS = {
    "en": {
        # ... существующие ключи ...
        "promo_instruction": "ℹ️ Use: <code>/code CODE</code>",
        
        
        # ✅ ДОБАВЬТЕ ЭТИ НОВЫЕ КЛЮЧИ:
        "welcome": """👋 **Welcome to FoodWizard.pro!**\n🥕 **Have ingredients?**\nDictate or write them.\n⚡️ **Or say:**\n"Give me a recipe for [dish]\"""",
        "safety_refusal": "⚠️ I cannot generate this recipe due to content policy restrictions.",
        "error_generation": "❌ Failed to generate recipe. Please try again with different ingredients.",
        "error_voice_recognition": "❌ Could not recognize speech. Please try typing instead.",
        "error_session_expired": "🕒 Session expired. Please start again.",
        "trial_activated_notification": "🎁 **Premium Trial Activated!**\nYou now have 7 days of premium access.",
        "favorite_added": "✅ '{dish_name}' added to favorites!",
        "favorite_removed": "🗑 '{dish_name}' removed from favorites.",
        "error_not_enough_products": "🤔 Not enough ingredients. Please add more items.",
        "voice_recognized": "✅ Recognized: {text}",
        "choose_category": "📝 **Choose Category:**",
        "choose_dish": "🍳 **Choose Dish:** (Category: {category})",
        "start_manual": "✍️ Type or dictate your ingredients.",
        "help_title": "❓ **Help**",
        "help_text": "📝 Send ingredients (e.g., 'eggs, milk, flour') to get recipe ideas.\n🎤 Or send a voice message.\n🍳 Or ask directly: 'Recipe for pancakes'.",
    },

    "de": {
        "welcome": """👋 **Willkommen!**\n🥕 **Haben Sie Zutaten?**\nSchreiben oder sprechen Sie.\n⚡️ **Oder:**\n"Rezept für [Gericht]" """,
        "lang_en": "🇬🇧 Englisch", "lang_de": "🇩🇪 Deutsch", "lang_fr": "🇫🇷 Französisch", "lang_it": "🇮🇹 Italienisch", "lang_es": "🇪🇸 Spanisch",
        "welcome": """👋 **Willkommen!**\n🥕 **Haben Sie Zutaten?**\nSchreiben oder sprechen Sie.\n⚡️ **Oder:**\n"Rezept für [Gericht]" """,
        "menu": "🍴 **Hauptmenü**", "choose_language": "🌐 **Sprache:**", "processing": "⏳ Moment...",
        "btn_favorites": "⭐️ Favoriten", "btn_restart": "🔄 Neustart", "btn_change_lang": "🌐 Sprache", "btn_help": "❓ Hilfe",
        "btn_add_to_fav": "☆ Speichern", "btn_remove_from_fav": "🌟 Gespeichert", "btn_back": "⬅️ Zurück", "btn_another": "➡️ Noch eins", "btn_buy_premium": "💎 Premium",
        "choose_category": "📝 **Kategorie:**", "choose_dish": "🍳 **Gericht:**",
        "favorites_title": "⭐️ **Favoriten**", "favorites_empty": "😔 Leer.",
        "premium_description": PREMIUM_DESC_DE,
        "lang_changed": "🌐 Sprache: Deutsch", "promo_instruction": "ℹ️ Benutze: <code>/code CODE</code>",
        # Для категорий копируем EN в цикле ниже, или можно перевести:
        "soup": "🍜 Suppen", "main": "🥩 Hauptgerichte", "salad": "🥗 Salate", 
        "breakfast": "🥞 Frühstücke", "dessert": "🍰 Desserts", "drink": "🍹 Getränke", "snack": "🥨 Snacks"
    },

    "fr": {
        "welcome": """👋 **Bienvenue !**\n🥕 **Ingrédients ?**\nÉcrivez ou dictez.\n⚡️ **Ou :**\n"Recette de [plat]" """,
        "lang_en": "🇬🇧 Anglais", "lang_de": "🇩🇪 Allemand", "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italien", "lang_es": "🇪🇸 Espagnol",
        "welcome": """👋 **Bienvenue !**\n🥕 **Ingrédients ?**\nÉcrivez ou dictez.\n⚡️ **Ou :**\n"Recette de [plat]" """,
        "menu": "🍴 **Menu**", "choose_language": "🌐 **Langue :**", "processing": "⏳ Attente...",
        "btn_favorites": "⭐️ Favoris", "btn_restart": "🔄 Redémarrer", "btn_change_lang": "🌐 Langue", "btn_help": "❓ Aide",
        "btn_add_to_fav": "☆ Sauvegarder", "btn_remove_from_fav": "🌟 Enregistré", "btn_back": "⬅️ Retour", "btn_another": "➡️ Autre", "btn_buy_premium": "💎 Premium",
        "choose_category": "📝 **Catégorie :**", "choose_dish": "🍳 **Plat :**",
        "favorites_title": "⭐️ **Favoris**", "favorites_empty": "😔 Vide.",
        "premium_description": PREMIUM_DESC_FR,
        "lang_changed": "🌐 Langue : Français", "promo_instruction": "ℹ️ Utilisez : <code>/code CODE</code>",
        "soup": "🍜 Soupes", "main": "🥩 Plats", "salad": "🥗 Salades", 
        "breakfast": "🥞 Petit-déj", "dessert": "🍰 Desserts", "drink": "🍹 Boissons", "snack": "🥨 Snacks"
    },
    
    "es": {
         "welcome": """👋 **¡Hola!**\n🥕 **¿Ingredientes?**\nEscribe o dicta.\n⚡️ **O:**\n"Receta de [plato]" """,
         "lang_en": "🇬🇧 Inglés", "lang_de": "🇩🇪 Alemán", "lang_fr": "🇫🇷 Francés", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español",
         "welcome": """👋 **¡Hola!**\n🥕 **¿Ingredientes?**\nEscribe o dicta.\n⚡️ **O:**\n"Receta de [plato]" """,
         "menu": "🍴 **Menú**", "choose_language": "🌐 **Idioma:**", "processing": "⏳ Pensando...",
         "btn_favorites": "⭐️ Favoritos", "btn_restart": "🔄 Reiniciar", "btn_change_lang": "🌐 Idioma", "btn_help": "❓ Ayuda",
         "btn_add_to_fav": "☆ Guardar", "btn_remove_from_fav": "🌟 Guardado", "btn_back": "⬅️ Atrás", "btn_another": "➡️ Otro", "btn_buy_premium": "💎 Premium",
         "choose_category": "📝 **Categoría:**", "choose_dish": "🍳 **Plato:**",
         "favorites_title": "⭐️ **Favoritos**", "favorites_empty": "😔 Vacío.",
         "premium_description": PREMIUM_DESC_ES,
         "lang_changed": "🌐 Idioma: Español", "promo_instruction": "ℹ️ Usa: <code>/code CODE</code>",
         "soup": "🍜 Sopas", "main": "🥩 Platos", "salad": "🥗 Ensaladas", 
         "breakfast": "🥞 Desayuno", "dessert": "🍰 Postres", "drink": "🍹 Bebidas", "snack": "🥨 Snacks"
    },
    
    "it": {
         "welcome": """👋 **Ciao!**\n🥕 **Ingredienti?**\nScrivi o detta.\n⚡️ **O:**\n"Ricetta di [piatto]" """,
         "lang_en": "🇬🇧 Inglese", "lang_de": "🇩🇪 Tedesco", "lang_fr": "🇫🇷 Francese", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Spagnolo",
         "welcome": """👋 **Ciao!**\n🥕 **Ingredienti?**\nScrivi o detta.\n⚡️ **O:**\n"Ricetta di [piatto]" """,
         "menu": "🍴 **Menu**", "choose_language": "🌐 **Lingua:**", "processing": "⏳ Attendo...",
         "btn_favorites": "⭐️ Preferiti", "btn_restart": "🔄 Riavvia", "btn_change_lang": "🌐 Lingua", "btn_help": "❓ Aiuto",
         "btn_add_to_fav": "☆ Salva", "btn_remove_from_fav": "🌟 Salvato", "btn_back": "⬅️ Indietro", "btn_another": "➡️ Altro", "btn_buy_premium": "💎 Premium",
         "choose_category": "📝 **Categoria:**", "choose_dish": "🍳 **Piatto:**",
         "favorites_title": "⭐️ **Preferiti**", "favorites_empty": "😔 Vuota.",
         "premium_description": PREMIUM_DESC_IT,
         "lang_changed": "🌐 Lingua: Italiano", "promo_instruction": "ℹ️ Usa: <code>/code CODE</code>",
         "soup": "🍜 Zuppe", "main": "🥩 Secondi", "salad": "🥗 Insalate", 
         "breakfast": "🥞 Colazione", "dessert": "🍰 Dessert", "drink": "🍹 Bevande", "snack": "🥨 Snack"
    }
}

# --- COPY FALLBACKS FROM EN ---
base_lang = TEXTS["en"]
for lang in ["de", "fr", "it", "es"]:
    for key, val in base_lang.items():
        if key not in TEXTS[lang]:
            TEXTS[lang][key] = val

def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in TEXTS: lang = "en"
    text = TEXTS[lang].get(key, TEXTS["en"].get(key, ""))
    if kwargs and text:
        try: return text.format(**kwargs)
        except: return text
    return text
