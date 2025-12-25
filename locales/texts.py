from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# --- ОПИСАНИЯ ПРЕМИУМА (Переведены) ---

PREMIUM_DESC_EN = """💎 **Premium Benefits:**

✅ **Favorites:** Unlimited saving
✅ **Health:** Nutrition facts (Calories/Macros)
✅ **Limits:** 100 text / 50 voice (daily)
✅ **Ingredients:** Up to 50 per request
✅ **Support:** Priority support

👇 **Choose a plan:**"""

PREMIUM_DESC_DE = """💎 **Premium-Vorteile:**

✅ **Favoriten:** Unbegrenzt speichern
✅ **Gesundheit:** Nährwertangaben (Kalorien/Makros)
✅ **Limits:** 100 Text / 50 Sprache (täglich)
✅ **Zutaten:** Bis zu 50 pro Anfrage
✅ **Support:** Priorisierter Support

👇 **Wählen Sie einen Plan:**"""

PREMIUM_DESC_FR = """💎 **Avantages Premium :**

✅ **Favoris :** Sauvegarde illimitée
✅ **Santé :** Infos nutritionnelles (Calories)
✅ **Limites :** 100 texte / 50 voix (par jour)
✅ **Ingrédients :** Jusqu'à 50 par demande
✅ **Support :** Support prioritaire

👇 **Choisissez un plan :**"""

PREMIUM_DESC_IT = """💎 **Vantaggi Premium:**

✅ **Preferiti:** Salvataggio illimitato
✅ **Salute:** Valori nutrizionali (Calorie)
✅ **Limiti:** 100 testo / 50 vocale (giornalieri)
✅ **Ingredienti:** Fino a 50 per richiesta
✅ **Supporto:** Supporto prioritario

👇 **Scegli un piano:**"""

PREMIUM_DESC_ES = """💎 **Beneficios Premium:**

✅ **Favoritos:** Guardado ilimitado
✅ **Salud:** Información nutricional (Calorías)
✅ **Límites:** 100 texto / 50 voz (diarios)
✅ **Ingredientes:** Hasta 50 por petición
✅ **Soporte:** Soporte prioritario

👇 **Elige un plan:**"""


TEXTS: Dict[str, Dict[str, str]] = {
    # ================= АНГЛИЙСКИЙ (EN - DEFAULT) =================
    "en": {
        "lang_en": "🇬🇧 English", "lang_de": "🇩🇪 Deutsch",
        "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español",

        "welcome": """👋 Hello.

🎤 Send a voice or text message listing your ingredients, and I'll suggest what you can cook with them.

📝 Or write "Give me a recipe for [dish]".""",
        
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
        "recipe_error": "❌ Could not generate recipe. Try again.",
        "dish_list_error": "❌ Could not get dish list.",
        "error_session_expired": "Session expired. Please send ingredients again.",
        
        "favorites_title": "⭐️ **Your Favorites**",
        "favorites_empty": "😔 Favorites list is empty.",
        "favorite_added": "⭐ Saved!", "favorite_removed": "🗑 Removed.",
        "favorite_limit": "❌ Limit reached ({limit}).",
        "favorites_list": "⭐️ **Favorites** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (from {date})\n",
        
        "premium_required_title": "💎 **Premium Required**",
        "premium_required_text": "The **Favorites** feature is limited in the free version. Upgrade to save more.",
        "premium_description": PREMIUM_DESC_EN,

        "limit_favorites_exceeded": "🔒 **Favorites limit reached!**\n\nFree version allows 3 recipes. Get Premium for unlimited storage and Nutrition facts.",
        "welcome_gift_alert": "🎁 **A Gift for New Friends!**\n\nUse the bot, and in 48 hours I'll gift you **7 Days of Premium** to try Nutrition facts and unlimited access. Stay tuned! 😉",
        "trial_activated_notification": "🎁 **Your Gift is Active!**\n\nYou've got 7 Days of Premium.\nNow available:\n✅ Nutrition Facts\n✅ Unlimited Favorites\n✅ 50 Voice requests\n\nTry cooking something special!",
        
        "limit_voice_exceeded": "❌ **Voice limit exceeded!**\n💎 Get Premium.",
        "limit_text_exceeded": "❌ **Text limit exceeded!**\n💎 Get Premium.",
        "error_voice_recognition": "🗣️ **Voice error.** Please speak clearly.",
        "error_generation": "❌ An error occurred.",
        "error_unknown": "❌ Unknown error.",
        "error_not_enough_products": "🤔 I need more ingredients to suggest a recipe. Please list at least 2-3 items.",
        "voice_recognized": "✅ Recognized: {text}",
        "lang_changed": "🌐 Language changed to English.",
        "safety_refusal": "🚫 I only cook food.",
        "help_title": "❓ **Help**",
        "help_text": "Just send a list of ingredients (text or voice).",
        "bot_description": "...", "bot_short_description": "...", "thanks": "😊", "easter_egg": "🥚",
    },

    # ================= НЕМЕЦКИЙ (DE) =================
    "de": {
        "lang_en": "🇬🇧 Englisch", "lang_de": "🇩🇪 Deutsch", "lang_fr": "🇫🇷 Französisch",
        "lang_it": "🇮🇹 Italienisch", "lang_es": "🇪🇸 Spanisch",

        "welcome": """👋 Hallo.

🎤 Senden Sie eine Sprach- oder Textnachricht mit Ihren Zutaten, und ich schlage vor, was Sie kochen können.

📝 Oder schreiben Sie "Gib mir ein Rezept für [Gericht]".""",

        "start_manual": "", "processing": "⏳ Ich denke nach...",
        "menu": "🍴 **Hauptmenü**", "choose_language": "🌐 **Sprache wählen:**",
        "soup": "🍜 Suppen", "main": "🥩 Hauptgerichte", "salad": "🥗 Salate",
        "breakfast": "🥞 Frühstücke", "dessert": "🍰 Desserts", "drink": "🍹 Getränke", "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoriten", "btn_restart": "🔄 Neustart",
        "btn_change_lang": "🌐 Sprache", "btn_help": "❓ Hilfe",
        "btn_add_to_fav": "☆ Speichern", "btn_remove_from_fav": "🌟 Gespeichert",
        "btn_back": "⬅️ Zurück", "btn_another": "➡️ Anderes Rezept",
        "btn_buy_premium": "💎 Premium Kaufen", "btn_page": "Seite {page}/{total}",
        
        "choose_category": "📝 **Kategorie wählen:**", "choose_dish": "🍳 **Gericht wählen:**",
        "recipe_error": "❌ Fehler beim Rezept.", "dish_list_error": "❌ Fehler bei der Liste.",
        "error_session_expired": "Sitzung abgelaufen. Bitte Zutaten erneut senden.",
        
        "favorites_title": "⭐️ **Favoriten**", "favorites_empty": "😔 Leer.",
        "favorite_added": "⭐ Gespeichert!", "favorite_removed": "🗑 Gelöscht.",
        "favorites_list": "⭐️ **Favoriten** (Seite {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (vom {date})\n",
        
        "premium_required_title": "💎 **Premium Erforderlich**",
        "premium_required_text": "Favoriten sind in der kostenlosen Version begrenzt.",
        "premium_description": PREMIUM_DESC_DE,
        "limit_favorites_exceeded": "🔒 **Favoritenlimit erreicht!**\n\nGratis: 3 Rezepte. Holen Sie sich Premium für unbegrenztes Speichern und Nährwerte.",
        
        "welcome_gift_alert": "🎁 **Geschenk!**\n\nIn 48 Stunden erhalten Sie **7 Tage Premium** gratis!",
        "trial_activated_notification": "🎁 **Geschenk aktiviert!**\n\n7 Tage Premium sind jetzt aktiv.\n✅ Nährwerte\n✅ Unbegrenzte Favoriten",

        "limit_voice_exceeded": "❌ **Sprachlimit erreicht!**", "limit_text_exceeded": "❌ **Textlimit erreicht!**",
        "error_voice_recognition": "🗣️ **Sprachfehler.**", "error_generation": "❌ Fehler.", "error_unknown": "❌ Fehler.",
        "error_not_enough_products": "🤔 Ich brauche mehr Zutaten.",
        "voice_recognized": "✅ Erkannt: {text}", "lang_changed": "🌐 Sprache: Deutsch.",
        "safety_refusal": "🚫 Nur Essen.", "help_title": "❓ **Hilfe**", "help_text": "Senden Sie eine Zutatenliste.",
    },

    # ================= ФРАНЦУЗСКИЙ (FR) =================
    "fr": {
        "lang_en": "🇬🇧 Anglais", "lang_de": "🇩🇪 Allemand", "lang_fr": "🇫🇷 Français",
        "lang_it": "🇮🇹 Italien", "lang_es": "🇪🇸 Espagnol",

        "welcome": """👋 Bonjour.

🎤 Envoyez un message vocal ou texte avec vos ingrédients, et je vous suggérerai quoi cuisiner.

📝 Ou écrivez "Donne-moi une recette de [plat]".""",

        "start_manual": "", "processing": "⏳ Je réfléchis...",
        "menu": "🍴 **Menu Principal**", "choose_language": "🌐 **Langue :**",
        "soup": "🍜 Soupes", "main": "🥩 Plats principaux", "salad": "🥗 Salades",
        "breakfast": "🥞 Petit-déj", "dessert": "🍰 Desserts", "drink": "🍹 Boissons", "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoris", "btn_restart": "🔄 Redémarrer",
        "btn_change_lang": "🌐 Langue", "btn_help": "❓ Aide",
        "btn_add_to_fav": "☆ Sauvegarder", "btn_remove_from_fav": "🌟 Enregistré",
        "btn_back": "⬅️ Retour", "btn_another": "➡️ Autre recette",
        "btn_buy_premium": "💎 Acheter Premium", "btn_page": "Page {page}/{total}",
        
        "choose_category": "📝 **Catégorie :**", "choose_dish": "🍳 **Plat :**",
        "recipe_error": "❌ Erreur recette.", "dish_list_error": "❌ Erreur liste.",
        "error_session_expired": "Session expirée. Renvoyez les ingrédients.",
        
        "favorites_title": "⭐️ **Vos Favoris**", "favorites_empty": "😔 Liste vide.",
        "favorite_added": "⭐ Sauvegardé !", "favorite_removed": "🗑 Supprimé.",
        "favorites_list": "⭐️ **Favoris** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (du {date})\n",

        "premium_required_title": "💎 **Premium Requis**",
        "premium_required_text": "Les favoris sont limités dans la version gratuite.",
        "premium_description": PREMIUM_DESC_FR,
        "limit_favorites_exceeded": "🔒 **Limite atteinte !**\n\nGratuit : 3 recettes. Prenez Premium pour l'illimité et les infos nutritionnelles.",

        "welcome_gift_alert": "🎁 **Cadeau !**\n\nDans 48h, vous recevrez **7 jours de Premium** gratuits !",
        "trial_activated_notification": "🎁 **Cadeau activé !**\n\n7 jours Premium actifs.\n✅ Infos nutritionnelles\n✅ Favoris illimités",
        
        "limit_voice_exceeded": "❌ **Limite vocale !**", "limit_text_exceeded": "❌ **Limite textuelle !**",
        "error_voice_recognition": "🗣️ **Erreur vocale.**", "error_generation": "❌ Erreur.", "error_unknown": "❌ Erreur.",
        "error_not_enough_products": "🤔 Il me faut plus d'ingrédients.",
        "voice_recognized": "✅ Reconnu : {text}", "lang_changed": "🌐 Langue : Français.",
        "safety_refusal": "🚫 Nourriture seulement.", "help_title": "❓ **Aide**", "help_text": "Envoyez une liste d'ingrédients.",
    },

    # ================= ИТАЛЬЯНСКИЙ (IT) =================
    "it": {
        "lang_en": "🇬🇧 Inglese", "lang_de": "🇩🇪 Tedesco", "lang_fr": "🇫🇷 Francese",
        "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Spagnolo",

        "welcome": """👋 Ciao.

🎤 Invia un messaggio vocale o di testo con gli ingredienti.

📝 O scrivi "Dammi una ricetta per [piatto]".""",

        "start_manual": "", "processing": "⏳ Sto pensando...",
        "menu": "🍴 **Menu Principale**", "choose_language": "🌐 **Lingua:**",
        "soup": "🍜 Zuppe", "main": "🥩 Secondi", "salad": "🥗 Insalate",
        "breakfast": "🥞 Colazione", "dessert": "🍰 Dessert", "drink": "🍹 Bevande", "snack": "🥨 Snack",
        
        "btn_favorites": "⭐️ Preferiti", "btn_restart": "🔄 Riavvia",
        "btn_change_lang": "🌐 Lingua", "btn_help": "❓ Aiuto",
        "btn_add_to_fav": "☆ Salva", "btn_remove_from_fav": "🌟 Salvato",
        "btn_back": "⬅️ Indietro", "btn_another": "➡️ Altra ricetta",
        "btn_buy_premium": "💎 Compra Premium", "btn_page": "Pag. {page}/{total}",
        
        "choose_category": "📝 **Categoria:**", "choose_dish": "🍳 **Piatto:**",
        "recipe_error": "❌ Errore ricetta.", "dish_list_error": "❌ Errore lista.",
        "error_session_expired": "Sessione scaduta. Reinvia gli ingredienti.",
        
        "favorites_title": "⭐️ **Preferiti**", "favorites_empty": "😔 Lista vuota.",
        "favorite_added": "⭐ Salvato!", "favorite_removed": "🗑 Rimosso.",
        "favorites_list": "⭐️ **Preferiti** (pag. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (del {date})\n",
        
        "premium_required_title": "💎 **Premium Richiesto**",
        "premium_required_text": "I preferiti sono limitati nella versione gratuita.",
        "premium_description": PREMIUM_DESC_IT,
        "limit_favorites_exceeded": "🔒 **Limite raggiunto!**\n\nGratis: 3 ricette. Passa a Premium per illimitato e valori nutrizionali.",

        "welcome_gift_alert": "🎁 **Regalo!**\n\nTra 48 ore riceverai **7 giorni di Premium** gratis!",
        "trial_activated_notification": "🎁 **Regalo attivo!**\n\n7 giorni Premium attivi.\n✅ Valori nutrizionali\n✅ Preferiti illimitati",
        
        "limit_voice_exceeded": "❌ **Limite vocale!**", "limit_text_exceeded": "❌ **Limite testo!**",
        "error_voice_recognition": "🗣️ **Errore vocale.**", "error_generation": "❌ Errore.", "error_unknown": "❌ Errore.",
        "error_not_enough_products": "🤔 Servono più ingredienti.",
        "voice_recognized": "✅ Riconosciuto: {text}", "lang_changed": "🌐 Lingua: Italiano.",
        "safety_refusal": "🚫 Solo cibo.", "help_title": "❓ **Aiuto**", "help_text": "Invia una lista di ingredienti.",
    },

    # ================= ИСПАНСКИЙ (ES) =================
    "es": {
        "lang_en": "🇬🇧 Inglés", "lang_de": "🇩🇪 Alemán", "lang_fr": "🇫🇷 Francés",
        "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español",

        "welcome": """👋 Hola.

🎤 Envía un mensaje de voz o texto con tus ingredientes.

📝 O escribe "Dame una receta de [plato]".""",

        "start_manual": "", "processing": "⏳ Pensando...",
        "menu": "🍴 **Menú Principal**", "choose_language": "🌐 **Idioma:**",
        "soup": "🍜 Sopas", "main": "🥩 Platos fuertes", "salad": "🥗 Ensaladas",
        "breakfast": "🥞 Desayunos", "dessert": "🍰 Postres", "drink": "🍹 Bebidas", "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoritos", "btn_restart": "🔄 Reiniciar",
        "btn_change_lang": "🌐 Idioma", "btn_help": "❓ Ayuda",
        "btn_add_to_fav": "☆ Guardar", "btn_remove_from_fav": "🌟 Guardado",
        "btn_back": "⬅️ Atrás", "btn_another": "➡️ Otra receta",
        "btn_buy_premium": "💎 Comprar Premium", "btn_page": "Pág. {page}/{total}",
        
        "choose_category": "📝 **Categoría:**", "choose_dish": "🍳 **Plato:**",
        "recipe_error": "❌ Error receta.", "dish_list_error": "❌ Error lista.",
        "error_session_expired": "Sesión expirada. Envía ingredientes de nuevo.",
        
        "favorites_title": "⭐️ **Favoritos**", "favorites_empty": "😔 Lista vacía.",
        "favorite_added": "⭐ ¡Guardado!", "favorite_removed": "🗑 Eliminado.",
        "favorites_list": "⭐️ **Favoritos** (pág. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (del {date})\n",
        
        "premium_required_title": "💎 **Premium Requerido**",
        "premium_required_text": "Favoritos limitados en versión gratuita.",
        "premium_description": PREMIUM_DESC_ES,
        "limit_favorites_exceeded": "🔒 **¡Límite alcanzado!**\n\nGratis: 3 recetas. Obtén Premium para ilimitado y nutrición.",

        "welcome_gift_alert": "🎁 **¡Regalo!**\n\nEn 48 horas recibirás **7 días Premium** gratis.",
        "trial_activated_notification": "🎁 **¡Regalo activo!**\n\n7 días Premium activos.\n✅ Nutrición\n✅ Favoritos ilimitados",
        
        "limit_voice_exceeded": "❌ **¡Límite voz!**", "limit_text_exceeded": "❌ **¡Límite texto!**",
        "error_voice_recognition": "🗣️ **Error voz.**", "error_generation": "❌ Error.", "error_unknown": "❌ Error.",
        "error_not_enough_products": "🤔 Necesito más ingredientes.",
        "voice_recognized": "✅ Reconocido: {text}", "lang_changed": "🌐 Idioma: Español.",
        "safety_refusal": "🚫 Solo comida.", "help_title": "❓ **Ayuda**", "help_text": "Envía una lista de ingredientes.",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    # 1. Проверяем, существует ли язык. Если нет - EN.
    if lang not in TEXTS: 
        lang = "en"
    
    lang_dict = TEXTS.get(lang, TEXTS["en"])
    
    # 2. Берем текст. Если ключа нет в текущем языке - берем из EN.
    # Если и в EN нет - возвращаем пустую строку (чтобы не падал код).
    text = lang_dict.get(key, TEXTS["en"].get(key, ""))
    
    if kwargs and text:
        try: return text.format(**kwargs)
        except KeyError: return text
    return text