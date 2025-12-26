from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# --- ОПИСАНИЯ ПРЕМИУМА ---
PREMIUM_DESC_EN = """💎 **Premium Benefits:**

✅ **Favorites:** Unlimited saving
✅ **Health:** Nutrition facts (Calories/Macros)
✅ **Limits:** 100 text / 50 voice (daily)
✅ **Ingredients:** Up to 50 per request
✅ **Support:** Priority support

👇 **Choose a plan:**"""

PREMIUM_DESC_DE = """💎 **Premium-Vorteile:**

✅ **Favoriten:** Unbegrenzt speichern
✅ **Gesundheit:** Nährwertangaben
✅ **Limits:** 100 Text / 50 Sprache
✅ **Support:** Priorisierter Support

👇 **Wählen Sie einen Plan:**"""

PREMIUM_DESC_FR = """💎 **Avantages Premium :**

✅ **Favoris :** Sauvegarde illimitée
✅ **Santé :** Infos nutritionnelles
✅ **Limites :** 100 texte / 50 voix
✅ **Support :** Support prioritaire

👇 **Choisissez un plan :**"""

PREMIUM_DESC_IT = """💎 **Vantaggi Premium:**

✅ **Preferiti:** Salvataggio illimitato
✅ **Salute:** Valori nutrizionali
✅ **Limiti:** 100 testo / 50 vocale
✅ **Supporto:** Supporto prioritario

👇 **Scegli un piano:**"""

PREMIUM_DESC_ES = """💎 **Beneficios Premium:**

✅ **Favoritos:** Guardado ilimitado
✅ **Salud:** Información nutricional
✅ **Límites:** 100 texto / 50 voz
✅ **Soporte:** Soporte prioritario

👇 **Elige un plan:**"""


TEXTS: Dict[str, Dict[str, str]] = {
    
    # ================= АНГЛИЙСКИЙ (EN - DEFAULT) =================
    "en": {
        # ИНСТРУКЦИЯ ПРОМОКОДА
        "promo_instruction": """ℹ️ **How to enter a Promo Code:**

Type the command followed by your code.

Example:
<code>/code FOOD2025</code>""",

        # НАЗВАНИЯ ЯЗЫКОВ
        "lang_en": "🇬🇧 English", "lang_de": "🇩🇪 German",
        "lang_fr": "🇫🇷 French", "lang_it": "🇮🇹 Italian", "lang_es": "🇪🇸 Spanish",

        "welcome": """👋 **Welcome to FoodWizard.pro!** 🧙‍♂️

🎤 Dictate (or write) a list of ingredients, and I'll suggest a meal.

⚡️ **Or give a direct command:**
— *"Give me a recipe for pancakes"*
— *"I want pizza"*

👇 Waiting for your ingredients!""",
        
        "start_manual": "", 
        "processing": "⏳ Thinking...",
        "menu": "🍴 **Main Menu**",
        "choose_language": "🌐 **Choose Language:**",
        "soup": "🍜 Soups", "main": "🥩 Main Courses", "salad": "🥗 Salads",
        "breakfast": "🥞 Breakfasts", "dessert": "🍰 Desserts", "drink": "🍹 Drinks", "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favorites", "btn_restart": "🔄 Restart",
        "btn_change_lang": "🌐 Language", "btn_help": "❓ Help",
        "btn_add_to_fav": "☆ Add to Favorites", "btn_remove_from_fav": "🌟 In Favorites",
        "btn_back": "⬅️ Back", "btn_another": "➡️ Another Recipe",
        "btn_buy_premium": "💎 Get Premium", "btn_page": "Page {page}/{total}",
        
        "choose_category": "📝 **Select a category:**",
        "choose_dish": "🍳 **Select a dish:**",
        "recipe_title": "✨ **Recipe: {dish_name}**",
        "recipe_ingredients": "🛒 **Ingredients:**",
        "recipe_instructions": "📝 **Instructions:**",
        "recipe_error": "❌ Could not generate recipe.",
        "dish_list_error": "❌ Could not get dish list.",
        "error_session_expired": "Session expired. Start over.",
        
        "favorites_title": "⭐️ **Your Favorites**",
        "favorites_empty": "😔 Favorites list is empty.",
        "favorite_added": "⭐ Recipe **{dish_name}** saved!",
        "favorite_removed": "🗑 Recipe **{dish_name}** removed.",
        "favorite_limit": "❌ Limit reached ({limit}).",
        "favorites_list": "⭐️ **Favorites** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (from {date})\n",
        
        "premium_required_title": "💎 **Premium Required**",
        "premium_required_text": "The **Favorites** feature is limited in the free version.",
        "premium_description": PREMIUM_DESC_EN,
        "limit_favorites_exceeded": "🔒 **Limit reached!**\n\nFree version: 3 recipes. Get Premium for unlimited storage.",
        
        "welcome_gift_alert": "🎁 **Gift from FoodWizard.pro!**\n\nIn 48 hours you will receive **7 Days of Premium** for free! Stay tuned. 😉",
        "trial_activated_notification": "🎁 **Your Gift is Active!**\n\n7 Days of Premium activated.\n✅ Nutrition Facts\n✅ Unlimited Favorites\n✅ 50 Voice requests",

        "limit_voice_exceeded": "❌ **Voice limit exceeded!**\n💎 Get Premium.",
        "limit_text_exceeded": "❌ **Text limit exceeded!**\n💎 Get Premium.",
        "error_voice_recognition": "🗣️ **Voice error.**",
        "error_generation": "❌ Error.",
        "error_unknown": "❌ Error.",
        "error_not_enough_products": "🤔 Need more ingredients.",
        "voice_recognized": "✅ Recognized: {text}",
        "lang_changed": "🌐 Language changed to English.",
        "safety_refusal": "🚫 Food only.",
        "help_title": "❓ **Help**",
        "help_text": "Send ingredients or ask 'Recipe for...'.",
        "bot_description": "...", "bot_short_description": "...", "thanks": "😊", "easter_egg": "🥚",
    },
    
    # ================= НЕМЕЦКИЙ =================
    "de": {
        "premium_description": PREMIUM_DESC_DE,
        "promo_instruction": """ℹ️ **Promo-Code eingeben:**

Geben Sie den Befehl und dann Ihren Code ein.

Beispiel:
<code>/code FOOD2025</code>"""
    },

    # ================= ФРАНЦУЗСКИЙ =================
    "fr": {
        "premium_description": PREMIUM_DESC_FR,
        "promo_instruction": """ℹ️ **Comment saisir le code :**

Tapez la commande suivie de votre code.

Exemple :
<code>/code FOOD2025</code>"""
    },

    # ================= ИТАЛЬЯНСКИЙ =================
    "it": {
        "premium_description": PREMIUM_DESC_IT,
        "promo_instruction": """ℹ️ **Come inserire il codice:**

Digita il comando seguito dal tuo codice.

Esempio:
<code>/code FOOD2025</code>"""
    },

    # ================= ИСПАНСКИЙ =================
    "es": {
        "premium_description": PREMIUM_DESC_ES,
        "promo_instruction": """ℹ️ **Cómo canjear el código:**

Escribe el comando seguido de tu código.

Ejemplo:
<code>/code FOOD2025</code>"""
    }
}

# Заполняем пустоты (копируем остальные английские ключи в другие языки)
base_lang = TEXTS["en"]
for lang in ["de", "fr", "it", "es"]:
    current_desc = TEXTS[lang].get("premium_description")
    current_instr = TEXTS[lang].get("promo_instruction")
    
    # Копируем всё из EN
    for k, v in base_lang.items():
        if k not in TEXTS[lang]:
            TEXTS[lang][k] = v
            
    # Восстанавливаем переведенные части
    if current_desc: TEXTS[lang]["premium_description"] = current_desc
    if current_instr: TEXTS[lang]["promo_instruction"] = current_instr
    
    # Копируем названия языков для меню
    for l_key in ["lang_ru", "lang_en", "lang_de", "lang_fr", "lang_it", "lang_es"]:
        TEXTS[lang][l_key] = base_lang[l_key]

def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in TEXTS: lang = "en"
    lang_dict = TEXTS.get(lang, TEXTS["en"])
    text = lang_dict.get(key, TEXTS["en"].get(key, ""))
    
    if kwargs and text:
        try: return text.format(**kwargs)
        except KeyError: 
            return text
    return text