from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

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
        "menu": "🍴 **Что будем готовить?**",
        "choose_language": "🌐 **Выберите язык:**",
        
        "soup": "🍜 Супы", "main": "🥩 Вторые блюда", "salad": "🥗 Салаты",
        "breakfast": "🥞 Завтраки", "dessert": "🍰 Десерты", "drink": "🍹 Напитки", "snack": "🥨 Закуски",
        
        "btn_favorites": "⭐️ Избранное", "btn_restart": "🔄 Рестарт",
        "btn_change_lang": "🌐 Сменить язык", "btn_help": "❓ Помощь",
        "btn_add_to_fav": "☆ В избранное", "btn_remove_from_fav": "🌟 В избранном",
        "btn_back": "⬅️ Назад", "btn_another": "➡️ Ещё рецепт",
        "btn_buy_premium": "💎 Премиум", "btn_page": "Стр. {page}/{total}",
        
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
        
        "limit_voice_exceeded": "❌ **Лимит голосовых запросов исчерпан!**",
        "limit_text_exceeded": "❌ **Лимит текстовых запросов исчерпан!**",
        "error_voice_recognition": "🗣️ **Ошибка распознавания.** Говорите четче.",
        "error_generation": "❌ Произошла ошибка.",
        "error_unknown": "❌ Неизвестная ошибка.",
        "error_not_enough_products": "🤔 Не могу понять, что приготовить. Назовите больше продуктов.",
        "voice_recognized": "✅ Распознано: {text}",
        "lang_changed": "🌐 Язык успешно изменен на русский.",
        "safety_refusal": "🚫 Извините, я готовлю только еду.",
        "help_title": "❓ **Помощь**",
        "help_text": "Просто отправьте список продуктов, и я подберу рецепт.",
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
        "menu": "🍴 **What should we cook?**",
        "choose_language": "🌐 **Choose Language:**",
        
        "soup": "🍜 Soups", "main": "🥩 Main Courses", "salad": "🥗 Salads",
        "breakfast": "🥞 Breakfasts", "dessert": "🍰 Desserts", "drink": "🍹 Drinks", "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favorites", "btn_restart": "🔄 Restart",
        "btn_change_lang": "🌐 Language", "btn_help": "❓ Help",
        "btn_add_to_fav": "☆ Add to Favorites", "btn_remove_from_fav": "🌟 In Favorites",
        "btn_back": "⬅️ Back", "btn_another": "➡️ Another Recipe",
        "btn_buy_premium": "💎 Premium", "btn_page": "Page {page}/{total}",
        
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
        
        "limit_voice_exceeded": "❌ **Voice limit exceeded!**",
        "limit_text_exceeded": "❌ **Text limit exceeded!**",
        "error_voice_recognition": "🗣️ **Voice error.** Speak clearer.",
        "error_generation": "❌ An error occurred.",
        "error_unknown": "❌ Unknown error.",
        "error_not_enough_products": "🤔 Need more ingredients.",
        "voice_recognized": "✅ Recognized: {text}",
        "lang_changed": "🌐 Language changed to English.",
        "safety_refusal": "🚫 I only cook food.",
        "help_title": "❓ **Help**",
        "help_text": "Just send a list of ingredients.",
    },

    # ================= НЕМЕЦКИЙ (DE) =================
    "de": {
        "lang_ru": "🇷🇺 Russisch", "lang_en": "🇬🇧 Englisch", "lang_de": "🇩🇪 Deutsch",
        "lang_fr": "🇫🇷 Französisch", "lang_it": "🇮🇹 Italienisch", "lang_es": "🇪🇸 Spanisch",

        "welcome": """👋 Hallo.

🎤 Senden Sie eine Sprach- oder Textnachricht mit Ihren Zutaten, und ich schlage vor, was Sie kochen können.

📝 Oder schreiben Sie "Gib mir ein Rezept für [Gericht]".""",

        "start_manual": "", "processing": "⏳ Ich denke nach...",
        "choose_language": "🌐 **Sprache wählen:**",
        "soup": "🍜 Suppen", "main": "🥩 Hauptgerichte", "salad": "🥗 Salate",
        "breakfast": "🥞 Frühstücke", "dessert": "🍰 Desserts", "drink": "🍹 Getränke", "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoriten", "btn_restart": "🔄 Neustart",
        "btn_change_lang": "🌐 Sprache", "btn_help": "❓ Hilfe",
        "btn_add_to_fav": "☆ Speichern", "btn_remove_from_fav": "🌟 Gespeichert",
        "btn_back": "⬅️ Zurück", "btn_another": "➡️ Anderes Rezept",
        "btn_buy_premium": "💎 Premium", "btn_page": "Seite {page}/{total}",
        
        "choose_category": "📝 **Kategorie wählen:**", "choose_dish": "🍳 **Gericht wählen:**",
        "recipe_error": "❌ Fehler beim Rezept.", "favorites_empty": "😔 Liste leer.",
        "favorite_added": "⭐ Gespeichert!", "favorite_removed": "🗑 Gelöscht.",
        "favorites_title": "⭐️ **Favoriten**", 
        "favorites_list": "⭐️ **Favoriten** (Seite {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (vom {date})\n",
        
        "limit_voice_exceeded": "❌ **Sprachlimit erreicht!**",
        "limit_text_exceeded": "❌ **Textlimit erreicht!**",
        "error_voice_recognition": "🗣️ **Sprachfehler.**",
        "error_generation": "❌ Fehler.", "error_not_enough_products": "🤔 Mehr Zutaten bitte.",
        "voice_recognized": "✅ Erkannt: {text}",
        "lang_changed": "🌐 Sprache: Deutsch.",
        "safety_refusal": "🚫 Ich koche nur Essen.",
        "help_title": "❓ **Hilfe**", "help_text": "Senden Sie eine Zutatenliste.",
    },

    # ================= ФРАНЦУЗСКИЙ (FR) =================
    "fr": {
        "lang_ru": "🇷🇺 Russe", "lang_en": "🇬🇧 Anglais", "lang_de": "🇩🇪 Allemand",
        "lang_fr": "🇫🇷 Français", "lang_it": "🇮🇹 Italien", "lang_es": "🇪🇸 Espagnol",

        "welcome": """👋 Bonjour.

🎤 Envoyez un message vocal ou texte avec vos ingrédients, et je vous suggérerai quoi cuisiner.

📝 Ou écrivez "Donne-moi une recette de [plat]".""",

        "start_manual": "", "processing": "⏳ Je réfléchis...",
        "choose_language": "🌐 **Langue :**",
        "soup": "🍜 Soupes", "main": "🥩 Plats principaux", "salad": "🥗 Salades",
        "breakfast": "🥞 Petit-déj", "dessert": "🍰 Desserts", "drink": "🍹 Boissons", "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoris", "btn_restart": "🔄 Redémarrer",
        "btn_change_lang": "🌐 Langue", "btn_help": "❓ Aide",
        "btn_add_to_fav": "☆ Sauvegarder", "btn_remove_from_fav": "🌟 Enregistré",
        "btn_back": "⬅️ Retour", "btn_another": "➡️ Autre recette",
        "btn_buy_premium": "💎 Premium", "btn_page": "Page {page}/{total}",
        
        "choose_category": "📝 **Catégorie :**", "choose_dish": "🍳 **Plat :**",
        "recipe_error": "❌ Erreur recette.", "favorites_empty": "😔 Liste vide.",
        "favorite_added": "⭐ Sauvegardé !", "favorite_removed": "🗑 Supprimé.",
        "favorites_title": "⭐️ **Vos Favoris**",
        "favorites_list": "⭐️ **Favoris** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (du {date})\n",
        
        "limit_voice_exceeded": "❌ **Limite vocale !**",
        "limit_text_exceeded": "❌ **Limite textuelle !**",
        "error_voice_recognition": "🗣️ **Erreur vocale.**",
        "error_generation": "❌ Erreur.", "error_not_enough_products": "🤔 Plus d'ingrédients SVP.",
        "voice_recognized": "✅ Reconnu : {text}",
        "lang_changed": "🌐 Langue : Français.",
        "safety_refusal": "🚫 Je ne cuisine que de la nourriture.",
        "help_title": "❓ **Aide**", "help_text": "Envoyez une liste d'ingrédients.",
    },

    # ================= ИТАЛЬЯНСКИЙ (IT) =================
    "it": {
        "lang_ru": "🇷🇺 Russo", "lang_en": "🇬🇧 Inglese", "lang_de": "🇩🇪 Tedesco",
        "lang_fr": "🇫🇷 Francese", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Spagnolo",

        "welcome": """👋 Ciao.

🎤 Invia un messaggio vocale o di testo con i tuoi ingredienti e ti suggerirò cosa cucinare.

📝 O scrivi "Dammi una ricetta per [piatto]".""",

        "start_manual": "", "processing": "⏳ Sto pensando...",
        "choose_language": "🌐 **Lingua:**",
        "soup": "🍜 Zuppe", "main": "🥩 Secondi", "salad": "🥗 Insalate",
        "breakfast": "🥞 Colazione", "dessert": "🍰 Dessert", "drink": "🍹 Bevande", "snack": "🥨 Snack",
        
        "btn_favorites": "⭐️ Preferiti", "btn_restart": "🔄 Riavvia",
        "btn_change_lang": "🌐 Lingua", "btn_help": "❓ Aiuto",
        "btn_add_to_fav": "☆ Salva", "btn_remove_from_fav": "🌟 Salvato",
        "btn_back": "⬅️ Indietro", "btn_another": "➡️ Altra ricetta",
        "btn_buy_premium": "💎 Premium", "btn_page": "Pag. {page}/{total}",
        
        "choose_category": "📝 **Categoria:**", "choose_dish": "🍳 **Piatto:**",
        "recipe_error": "❌ Errore ricetta.", "favorites_empty": "😔 Lista vuota.",
        "favorite_added": "⭐ Salvato!", "favorite_removed": "🗑 Rimosso.",
        "favorites_title": "⭐️ **Preferiti**",
        "favorites_list": "⭐️ **Preferiti** (pag. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (del {date})\n",
        
        "limit_voice_exceeded": "❌ **Limite vocale!**",
        "limit_text_exceeded": "❌ **Limite testo!**",
        "error_voice_recognition": "🗣️ **Errore vocale.**",
        "error_generation": "❌ Errore.", "error_not_enough_products": "🤔 Più ingredienti per favore.",
        "voice_recognized": "✅ Riconosciuto: {text}",
        "lang_changed": "🌐 Lingua: Italiano.",
        "safety_refusal": "🚫 Cucino solo cibo.",
        "help_title": "❓ **Aiuto**", "help_text": "Invia una lista di ingredienti.",
    },

    # ================= ИСПАНСКИЙ (ES) =================
    "es": {
        "lang_ru": "🇷🇺 Ruso", "lang_en": "🇬🇧 Inglés", "lang_de": "🇩🇪 Alemán",
        "lang_fr": "🇫🇷 Francés", "lang_it": "🇮🇹 Italiano", "lang_es": "🇪🇸 Español",

        "welcome": """👋 Hola.

🎤 Envía un mensaje de voz o texto con tus ingredientes y te sugeriré qué cocinar.

📝 O escribe "Dame una receta de [plato]".""",

        "start_manual": "", "processing": "⏳ Pensando...",
        "choose_language": "🌐 **Idioma:**",
        "soup": "🍜 Sopas", "main": "🥩 Platos fuertes", "salad": "🥗 Ensaladas",
        "breakfast": "🥞 Desayunos", "dessert": "🍰 Postres", "drink": "🍹 Bebidas", "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoritos", "btn_restart": "🔄 Reiniciar",
        "btn_change_lang": "🌐 Idioma", "btn_help": "❓ Ayuda",
        "btn_add_to_fav": "☆ Guardar", "btn_remove_from_fav": "🌟 Guardado",
        "btn_back": "⬅️ Atrás", "btn_another": "➡️ Otra receta",
        "btn_buy_premium": "💎 Premium", "btn_page": "Pág. {page}/{total}",
        
        "choose_category": "📝 **Categoría:**", "choose_dish": "🍳 **Plato:**",
        "recipe_error": "❌ Error de receta.", "favorites_empty": "😔 Lista vacía.",
        "favorite_added": "⭐ ¡Guardado!", "favorite_removed": "🗑 Eliminado.",
        "favorites_title": "⭐️ **Tus Favoritos**",
        "favorites_list": "⭐️ **Favoritos** (pág. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (del {date})\n",
        
        "limit_voice_exceeded": "❌ **¡Límite de voz!**",
        "limit_text_exceeded": "❌ **¡Límite de texto!**",
        "error_voice_recognition": "🗣️ **Error de voz.**",
        "error_generation": "❌ Error.", "error_not_enough_products": "🤔 Más ingredientes por favor.",
        "voice_recognized": "✅ Reconocido: {text}",
        "lang_changed": "🌐 Idioma: Español.",
        "safety_refusal": "🚫 Solo cocino comida.",
        "help_title": "❓ **Ayuda**", "help_text": "Envía una lista de ingredientes.",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in TEXTS: lang = "ru"
    lang_dict = TEXTS.get(lang, TEXTS["ru"])
    text = lang_dict.get(key, TEXTS["ru"].get(key, ""))
    if kwargs and text:
        try: return text.format(**kwargs)
        except KeyError: return text
    return text