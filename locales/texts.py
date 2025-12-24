from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# --- ОПИСАНИЯ ПРЕМИУМА (С шаблонами) ---
PREMIUM_DESC_RU = """💎 **Преимущества Premium:**

✅ **Избранное:** Сохраняйте любые рецепты
✅ **Лимиты:** 100 текст / 50 голос (в день)
✅ **Ингредиенты:** До 50 в запросе
✅ **Поддержка:** Приоритетная помощь

👇 **Выберите тариф:**"""

PREMIUM_DESC_EN = """💎 **Premium Benefits:**

✅ **Favorites:** Save unlimited recipes
✅ **Limits:** 100 text / 50 voice (daily)
✅ **Ingredients:** Up to 50 per request
✅ **Support:** Priority support

👇 **Choose a plan:**"""

PREMIUM_DESC_DE = """💎 **Premium-Vorteile:**

✅ **Favoriten:** Unbegrenzt speichern
✅ **Limits:** 100 Text / 50 Sprache (täglich)
✅ **Zutaten:** Bis zu 50 pro Anfrage
✅ **Support:** Priorisierter Support

👇 **Wählen Sie einen Plan:**"""

PREMIUM_DESC_FR = """💎 **Avantages Premium:**

✅ **Favoris:** Sauvegarde illimitée
✅ **Limites:** 100 texte / 50 voix (par jour)
✅ **Ingrédients:** Jusqu'à 50 par demande
✅ **Support:** Support prioritaire

👇 **Choisissez un plan:**"""

PREMIUM_DESC_IT = """💎 **Vantaggi Premium:**

✅ **Preferiti:** Salvataggio illimitato
✅ **Limiti:** 100 testo / 50 vocale (giornalieri)
✅ **Ingredienti:** Fino a 50 per richiesta
✅ **Supporto:** Supporto prioritario

👇 **Scegli un piano:**"""

PREMIUM_DESC_ES = """💎 **Beneficios Premium:**

✅ **Favoritos:** Guardado ilimitado
✅ **Límites:** 100 texto / 50 voz (diarios)
✅ **Ingredientes:** Hasta 50 por petición
✅ **Soporte:** Soporte prioritario

👇 **Elige un plan:**"""


TEXTS: Dict[str, Dict[str, str]] = {
    # ================= РУССКИЙ (RU) =================
    "ru": {
        "lang_ru": "🇷🇺 Русский", "lang_en": "🇬🇧 English", "lang_de": "🇩🇪 Deutsch",
        "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español",

        "welcome": """👋 Здравствуйте.

🎤 Отправьте голосовое или текстовое сообщение с перечнем продуктов, и я подскажу, что из них можно приготовить.

📝 Или напишите "Дай рецепт [блюдо]".""",
        
        "start_manual": "", 
        "processing": "⏳ Думаю...",
        "menu": "🍴 **Главное меню**",
        "choose_language": "🌐 **Выберите язык:**",
        
        "soup": "🍜 Супы", "main": "🥩 Вторые блюда", "salad": "🥗 Салаты",
        "breakfast": "🥞 Завтраки", "dessert": "🍰 Десерты", "drink": "🍹 Напитки", "snack": "🥨 Закуски",
        
        "btn_favorites": "⭐️ Избранное",
        "btn_restart": "🔄 Рестарт",
        "btn_change_lang": "🌐 Язык",
        "btn_help": "❓ Помощь",
        "btn_add_to_fav": "☆ В избранное",
        "btn_remove_from_fav": "🌟 В избранном",
        "btn_back": "⬅️ Назад",
        "btn_another": "➡️ Ещё рецепт",
        "btn_buy_premium": "💎 Купить Премиум",
        "btn_page": "Стр. {page}/{total}",
        
        "choose_category": "📝 **Выберите категорию блюд:**",
        "choose_dish": "🍳 **Выберите блюдо:**",
        "recipe_title": "✨ **Рецепт: {dish_name}**",
        "recipe_ingredients": "🛒 **Ингредиенты:**",
        "recipe_instructions": "📝 **Инструкция:**",
        "recipe_error": "❌ Не удалось сгенерировать рецепт.",
        "dish_list_error": "❌ Не удалось получить список блюд.",
        "error_session_expired": "Время сессии истекло. Начните заново.",
        
        "favorites_title": "⭐️ **Ваши избранные рецепты**",
        "favorites_empty": "😔 Список избранного пуст.",
        "favorite_added": "⭐ Рецепт **{dish_name}** добавлен в избранное!",
        "favorite_removed": "🗑 Рецепт **{dish_name}** удален из избранного.",
        "favorite_limit": "❌ Достигнут лимит избранных рецептов ({limit}).",
        "favorites_list": "⭐️ **Ваши избранные рецепты** (стр. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (от {date})\n",
        
        "premium_required_title": "💎 **Требуется Премиум**",
        "premium_required_text": "Функция **Избранное** доступна только для Премиум-пользователей.",
        "premium_description": PREMIUM_DESC_RU,

        "limit_voice_exceeded": "❌ **Лимит голосовых запросов исчерпан!**\n💎 Купите Премиум.",
        "limit_text_exceeded": "❌ **Лимит текстовых запросов исчерпан!**\n💎 Купите Премиум.",
        
        "error_voice_recognition": "🗣️ **Ошибка распознавания.**",
        "error_generation": "❌ Произошла ошибка.",
        "error_unknown": "❌ Неизвестная ошибка.",
        "error_not_enough_products": "🤔 Не могу понять, что приготовить.",
        "voice_recognized": "✅ Распознано: {text}",
        "lang_changed": "🌐 Язык изменен на Русский.",
        "safety_refusal": "🚫 Извините, я готовлю только еду.",
        "help_title": "❓ **Помощь**",
        "help_text": "Отправьте список продуктов, и я подберу рецепт.",
        "bot_description": "...", "bot_short_description": "...", "thanks": "😊", "easter_egg": "🥚",
    },
    
    # ================= АНГЛИЙСКИЙ (EN) =================
    "en": {
        "lang_ru": "🇷🇺 Russian", "lang_en": "🇬🇧 English", "lang_de": "🇩🇪 German",
        "lang_fr": "🇫🇷 French", "lang_it": "🇮🇹 Italian", "lang_es": "🇪🇸 Spanish",

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
        "btn_buy_premium": "💎 Get Premium",
        "btn_page": "Page {page}/{total}",
        
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
        "favorite_limit": "❌ Favorites limit reached ({limit}).",
        "favorites_list": "⭐️ **Favorites** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (from {date})\n",
        
        "premium_required_title": "💎 **Premium Required**",
        "premium_required_text": "The **Favorites** feature is available only for Premium users.",
        "premium_description": PREMIUM_DESC_EN,

        "limit_voice_exceeded": "❌ **Voice limit exceeded!**\n💎 Get Premium.",
        "limit_text_exceeded": "❌ **Text limit exceeded!**\n💎 Get Premium.",
        "error_voice_recognition": "🗣️ **Voice error.**",
        "error_generation": "❌ Error.",
        "error_unknown": "❌ Unknown error.",
        "error_not_enough_products": "🤔 Need more ingredients.",
        "voice_recognized": "✅ Recognized: {text}",
        "lang_changed": "🌐 Language changed to English.",
        "safety_refusal": "🚫 I only cook food.",
        "help_title": "❓ **Help**",
        "help_text": "Just send a list of ingredients.",
        "bot_description": "...", "bot_short_description": "...", "thanks": "😊", "easter_egg": "🥚",
    },
    
    # ================= НЕМЕЦКИЙ (DE) =================
    "de": {
        "lang_ru": "🇷🇺 Russisch", "lang_en": "🇬🇧 Englisch", "lang_de": "🇩🇪 Deutsch",
        "lang_fr": "🇫🇷 Französisch", "lang_it": "🇮🇹 Italienisch", "lang_es": "🇪🇸 Spanisch",

        "welcome": """👋 Hallo.

🎤 Senden Sie eine Sprach- oder Textnachricht mit Ihren Zutaten, und ich schlage vor, was Sie kochen können.

📝 Oder schreiben Sie "Gib mir ein Rezept für [Gericht]".""",

        "start_manual": "", "processing": "⏳ Ich denke nach...",
        "menu": "🍴 **Hauptmenü**",
        "choose_language": "🌐 **Sprache wählen:**",
        "soup": "🍜 Suppen", "main": "🥩 Hauptgerichte", "salad": "🥗 Salate",
        "breakfast": "🥞 Frühstücke", "dessert": "🍰 Desserts", "drink": "🍹 Getränke", "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoriten", "btn_restart": "🔄 Neustart",
        "btn_change_lang": "🌐 Sprache", "btn_help": "❓ Hilfe",
        "btn_add_to_fav": "☆ Speichern", "btn_remove_from_fav": "🌟 Gespeichert",
        "btn_back": "⬅️ Zurück", "btn_another": "➡️ Anderes Rezept",
        "btn_buy_premium": "💎 Premium Kaufen", "btn_page": "Seite {page}/{total}",
        
        "choose_category": "📝 **Kategorie wählen:**", "choose_dish": "🍳 **Gericht wählen:**",
        "recipe_error": "❌ Fehler beim Rezept.", "dish_list_error": "❌ Fehler bei der Liste.",
        "error_session_expired": "Sitzung abgelaufen. Neustart.",
        
        "favorites_title": "⭐️ **Favoriten**",
        "favorites_empty": "😔 Leer.",
        "favorite_added": "⭐ Gespeichert!", "favorite_removed": "🗑 Gelöscht.",
        "favorites_list": "⭐️ **Favoriten** (Seite {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (vom {date})\n",
        "favorite_limit": "❌ Limit erreicht ({limit}).",
        
        "premium_required_title": "💎 **Premium Erforderlich**",
        "premium_required_text": "Favoriten sind nur für Premium-Nutzer.",
        "premium_description": PREMIUM_DESC_DE,
        
        "limit_voice_exceeded": "❌ **Sprachlimit erreicht!**",
        "limit_text_exceeded": "❌ **Textlimit erreicht!**",
        "error_voice_recognition": "🗣️ **Sprachfehler.**",
        "error_generation": "❌ Fehler.", "error_unknown": "❌ Fehler.",
        "error_not_enough_products": "🤔 Mehr Zutaten bitte.",
        "voice_recognized": "✅ Erkannt: {text}",
        "lang_changed": "🌐 Sprache: Deutsch.",
        "safety_refusal": "🚫 Ich koche nur Essen.",
        "help_title": "❓ **Hilfe**", "help_text": "Senden Sie eine Zutatenliste.",
        "bot_description": "...", "bot_short_description": "...", "thanks": "😊", "easter_egg": "🥚",
    },

    # ================= ФРАНЦУЗСКИЙ (FR) =================
    "fr": {
        "lang_ru": "🇷🇺 Russe", "lang_en": "🇬🇧 Anglais", "lang_de": "🇩🇪 Allemand",
        "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italien", "lang_es": "🇪🇸 Espagnol",

        "welcome": """👋 Bonjour.

🎤 Envoyez un message vocal ou texte avec vos ingrédients, et je vous suggérerai quoi cuisiner.

📝 Ou écrivez "Donne-moi une recette de [plat]".""",

        "start_manual": "", "processing": "⏳ Je réfléchis...",
        "menu": "🍴 **Menu Principal**",
        "choose_language": "🌐 **Langue :**",
        "soup": "🍜 Soupes", "main": "🥩 Plats principaux", "salad": "🥗 Salades",
        "breakfast": "🥞 Petit-déj", "dessert": "🍰 Desserts", "drink": "🍹 Boissons", "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoris", "btn_restart": "🔄 Redémarrer",
        "btn_change_lang": "🌐 Langue", "btn_help": "❓ Aide",
        "btn_add_to_fav": "☆ Sauvegarder", "btn_remove_from_fav": "🌟 Enregistré",
        "btn_back": "⬅️ Retour", "btn_another": "➡️ Autre recette",
        "btn_buy_premium": "💎 Acheter Premium", "btn_page": "Page {page}/{total}",
        
        "choose_category": "📝 **Catégorie :**", "choose_dish": "🍳 **Plat :**",
        "recipe_error": "❌ Erreur recette.", "dish_list_error": "❌ Erreur liste.",
        "error_session_expired": "Session expirée. Recommencez.",
        
        "favorites_title": "⭐️ **Vos Favoris**",
        "favorites_empty": "😔 Liste vide.",
        "favorite_added": "⭐ Sauvegardé !", "favorite_removed": "🗑 Supprimé.",
        "favorite_limit": "❌ Limite atteinte ({limit}).",
        "favorites_list": "⭐️ **Favoris** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (du {date})\n",

        "premium_required_title": "💎 **Premium Requis**",
        "premium_required_text": "Les favoris sont réservés aux membres Premium.",
        "premium_description": PREMIUM_DESC_FR,
        
        "limit_voice_exceeded": "❌ **Limite vocale !**",
        "limit_text_exceeded": "❌ **Limite textuelle !**",
        "error_voice_recognition": "🗣️ **Erreur vocale.**",
        "error_generation": "❌ Erreur.", "error_unknown": "❌ Erreur.",
        "error_not_enough_products": "🤔 Plus d'ingrédients SVP.",
        "voice_recognized": "✅ Reconnu : {text}",
        "lang_changed": "🌐 Langue : Français.",
        "safety_refusal": "🚫 Je ne cuisine que de la nourriture.",
        "help_title": "❓ **Aide**", "help_text": "Envoyez une liste d'ingrédients.",
        "bot_description": "...", "bot_short_description": "...", "thanks": "😊", "easter_egg": "🥚",
    },

    # ================= ИТАЛЬЯНСКИЙ (IT) =================
    "it": {
        "lang_ru": "🇷🇺 Russo", "lang_en": "🇬🇧 Inglese", "lang_de": "🇩🇪 Tedesco",
        "lang_fr": "🇫🇷 Francese", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Spagnolo",

        "welcome": """👋 Ciao.

🎤 Invia un messaggio vocale o di testo con l'elenco dei tuoi ingredienti e ti suggerirò cosa cucinare.

📝 O scrivi "Dammi una ricetta per [piatto]".""",

        "start_manual": "", "processing": "⏳ Sto pensando...",
        "menu": "🍴 **Menu Principale**",
        "choose_language": "🌐 **Lingua:**",
        "soup": "🍜 Zuppe", "main": "🥩 Secondi", "salad": "🥗 Insalate",
        "breakfast": "🥞 Colazione", "dessert": "🍰 Dessert", "drink": "🍹 Bevande", "snack": "🥨 Snack",
        
        "btn_favorites": "⭐️ Preferiti", "btn_restart": "🔄 Riavvia",
        "btn_change_lang": "🌐 Lingua", "btn_help": "❓ Aiuto",
        "btn_add_to_fav": "☆ Salva", "btn_remove_from_fav": "🌟 Salvato",
        "btn_back": "⬅️ Indietro", "btn_another": "➡️ Altra ricetta",
        "btn_buy_premium": "💎 Compra Premium", "btn_page": "Pag. {page}/{total}",
        
        "choose_category": "📝 **Categoria:**", "choose_dish": "🍳 **Piatto:**",
        "recipe_error": "❌ Errore ricetta.", "dish_list_error": "❌ Errore lista.",
        "error_session_expired": "Sessione scaduta.",
        
        "favorites_title": "⭐️ **Preferiti**",
        "favorites_empty": "😔 Lista vuota.",
        "favorite_added": "⭐ Salvato!", "favorite_removed": "🗑 Rimosso.",
        "favorite_limit": "❌ Limite raggiunto ({limit}).",
        "favorites_list": "⭐️ **Preferiti** (pag. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (del {date})\n",
        
        "premium_required_title": "💎 **Premium Richiesto**",
        "premium_required_text": "I preferiti sono solo per utenti Premium.",
        "premium_description": PREMIUM_DESC_IT,
        
        "limit_voice_exceeded": "❌ **Limite vocale!**",
        "limit_text_exceeded": "❌ **Limite testo!**",
        "error_voice_recognition": "🗣️ **Errore vocale.**",
        "error_generation": "❌ Errore.", "error_unknown": "❌ Errore.",
        "error_not_enough_products": "🤔 Più ingredienti per favore.",
        "voice_recognized": "✅ Riconosciuto: {text}",
        "lang_changed": "🌐 Lingua: Italiano.",
        "safety_refusal": "🚫 Cucino solo cibo.",
        "help_title": "❓ **Aiuto**", "help_text": "Invia una lista di ingredienti.",
        "bot_description": "...", "bot_short_description": "...", "thanks": "😊", "easter_egg": "🥚",
    },

    # ================= ИСПАНСКИЙ (ES) =================
    "es": {
        "lang_ru": "🇷🇺 Ruso", "lang_en": "🇬🇧 Inglés", "lang_de": "🇩🇪 Alemán",
        "lang_fr": "🇫🇷 Francés", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español",

        "welcome": """👋 Hola.

🎤 Envía un mensaje de voz o texto con tus ingredientes y te sugeriré qué cocinar.

📝 O escribe "Dame una receta de [plato]".""",

        "start_manual": "", "processing": "⏳ Pensando...",
        "menu": "🍴 **Menú Principal**",
        "choose_language": "🌐 **Idioma:**",
        "soup": "🍜 Sopas", "main": "🥩 Platos fuertes", "salad": "🥗 Ensaladas",
        "breakfast": "🥞 Desayunos", "dessert": "🍰 Postres", "drink": "🍹 Bebidas", "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoritos", "btn_restart": "🔄 Reiniciar",
        "btn_change_lang": "🌐 Idioma", "btn_help": "❓ Ayuda",
        "btn_add_to_fav": "☆ Guardar", "btn_remove_from_fav": "🌟 Guardado",
        "btn_back": "⬅️ Atrás", "btn_another": "➡️ Otra receta",
        "btn_buy_premium": "💎 Comprar Premium", "btn_page": "Pág. {page}/{total}",
        
        "choose_category": "📝 **Categoría:**", "choose_dish": "🍳 **Plato:**",
        "recipe_error": "❌ Error receta.", "dish_list_error": "❌ Error lista.",
        "error_session_expired": "Sesión expirada.",
        
        "favorites_title": "⭐️ **Favoritos**",
        "favorites_empty": "😔 Lista vacía.",
        "favorite_added": "⭐ ¡Guardado!", "favorite_removed": "🗑 Eliminado.",
        "favorite_limit": "❌ Límite alcanzado ({limit}).",
        "favorites_list": "⭐️ **Favoritos** (pág. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (del {date})\n",
        
        "premium_required_title": "💎 **Premium Requerido**",
        "premium_required_text": "Favoritos solo para Premium.",
        "premium_description": PREMIUM_DESC_ES,
        
        "limit_voice_exceeded": "❌ **¡Límite de voz!**",
        "limit_text_exceeded": "❌ **¡Límite de texto!**",
        "error_voice_recognition": "🗣️ **Error de voz.**",
        "error_generation": "❌ Error.", "error_unknown": "❌ Error.",
        "error_not_enough_products": "🤔 Más ingredientes por favor.",
        "voice_recognized": "✅ Reconocido: {text}",
        "lang_changed": "🌐 Idioma: Español.",
        "safety_refusal": "🚫 Solo cocino comida.",
        "help_title": "❓ **Ayuda**", "help_text": "Envía una lista de ingredientes.",
        "bot_description": "...", "bot_short_description": "...", "thanks": "😊", "easter_egg": "🥚",
    }
}

# Функция получения текста
def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in TEXTS: lang = "ru"
    lang_dict = TEXTS.get(lang, TEXTS["ru"])
    # Фолбэк: Текущий язык -> Русский язык -> Пустая строка
    text = lang_dict.get(key, TEXTS["ru"].get(key, ""))
    
    if kwargs and text:
        try: return text.format(**kwargs)
        except KeyError: 
            logger.warning(f"Key error in text: {key}")
            return text
    return text