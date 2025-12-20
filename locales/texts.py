from typing import Dict, Any, List
import logging
from .prompts import PROMPTS as PROMPT_TEXTS # Для полноты картины, хотя не используется

logger = logging.getLogger(__name__)

TEXTS: Dict[str, Dict[str, str]] = {
    "ru": {
        # Интерфейс
        "welcome": "👋 Привет, {name}!\n\nЯ бот-шеф. Назови продукты, а я скажу, что из них приготовить.",
        "start_manual": "💬 **Отправьте голосовое или текстовое сообщение** с продуктами.\n📝 Или напишите **\"Дай рецепт [блюдо]\"**.",
        "processing": "⏳ Думаю...",
        "menu": "🍴 **Что будем готовить?**",
        "choose_language": "🌐 **Выберите язык:**",
        
        # Категории
        "soup": "🍜 Супы",
        "main": "🥩 Вторые блюда",
        "salad": "🥗 Салаты",
        "breakfast": "🥞 Завтраки",
        "dessert": "🍰 Десерты",
        "drink": "🍹 Напитки",
        "snack": "🥨 Закуски",
        
        # Кнопки
        "btn_favorites": "⭐️ Избранное",
        "btn_restart": "🔄 Рестарт",
        "btn_change_lang": "🌐 Сменить язык",
        "btn_help": "❓ Помощь",
        "btn_add_to_fav": "➕ Добавить в избранное",
        "btn_remove_from_fav": "✅ В избранном",
        "btn_back": "⬅️ Назад",
        "btn_another": "➡️ Ещё рецепт",
        "btn_buy_premium": "💎 Премиум",
        "btn_page": "Стр. {page}/{total}",
        
        # Рецепты и блюда
        "choose_category": "📝 **Выберите категорию блюд:**",
        "choose_dish": "🍳 **Выберите блюдо:**",
        "recipe_title": "✨ **Рецепт: {dish_name}**",
        "recipe_ingredients": "🛒 **Ингредиенты:**",
        "recipe_instructions": "📝 **Инструкция:**",
        "recipe_error": "❌ Не удалось сгенерировать рецепт. Попробуйте снова или выберите другое блюдо.",
        "dish_list_error": "❌ Не удалось получить список блюд. Попробуйте снова или измените продукты.",
        "error_session_expired": "Время сессии истекло. Пожалуйста, начните заново, отправив список продуктов.",
        
        # Избранное
        "favorites_title": "⭐️ **Ваши избранные рецепты**",
        "favorites_empty": "😔 Список избранного пуст.",
        "favorite_added": "✅ Рецепт **{dish_name}** добавлен в избранное!",
        "favorite_removed": "➖ Рецепт **{dish_name}** удален из избранного.",
        "favorite_limit": "❌ Достигнут лимит избранных рецептов ({limit}).",
        "favorites_list": "⭐️ **Ваши избранные рецепты** (стр. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (от {date})\n",
        
        # Ошибки и лимиты
        "limit_voice_exceeded": "❌ **Лимит голосовых запросов исчерпан!**\n\nВы использовали {used} из {limit} голосовых запросов сегодня. Лимиты обновляются каждый день в 00:00.\n\n💎 **Хотите больше?** Используйте команду /stats",
        "limit_text_exceeded": "❌ **Лимит текстовых запросов исчерпан!**\n\nВы использовали {used} из {limit} текстовых запросов сегодня. Лимиты обновляются каждый день в 00:00.\n\n💎 **Хотите больше?** Используйте команду /stats",
        "error_voice_recognition": "🗣️ **Ошибка распознавания голоса.** Пожалуйста, попробуйте говорить четче или используйте текстовый ввод.",
        "error_generation": "❌ Произошла ошибка. Попробуйте ещё раз.",
        "error_unknown": "❌ Произошла неизвестная ошибка.",
        "error_not_enough_products": "🤔 Не могу понять, что приготовить. Пожалуйста, назовите больше продуктов.",
        "voice_recognized": "✅ Распознано: {text}", # <-- ИСПРАВЛЕНО
        
        # Язык
        "lang_changed": "🌐 Язык успешно изменен на русский.",
        "lang_ru": "🇷🇺 Русский",
        "lang_en": "🇬🇧 English",
        "lang_de": "🇩🇪 Deutsch",
        "lang_fr": "🇫🇷 Français",
        "lang_it": "🇮🇹 Italiano",
        "lang_es": "🇪🇸 Español",
        
        # Помощь
        "help_title": "❓ **Помощь по Боту-Шефу**",
        "help_text": """
*Как использовать:*
1. Отправьте ингредиенты (текстом или голосом)
2. Выберите категорию блюда
3. Выберите блюдо из списка
4. Получите рецепт

*Команды:*
/start - начать заново
/favorites - избранные рецепты
/lang - сменить язык
/help - помощь
/stats - статистика и лимиты

*Советы:*
- Вы можете добавлять ингредиенты несколько раз
- Нажмите на ✅ под рецептом, чтобы сохранить
- Голосовые сообщения удаляются автоматически

*Поддержка:* @support
        """,
        
        "thanks": "😊 Пожалуйста! 🍽️",
        "easter_egg": "🥚 Вы нашли пасхальное яйцо!",
        "safety_refusal": "🚫 Извините, я готовлю только еду. Могу предложить рецепты блюд из разных кухонь мира! 🌍",
    },
    
    "en": {
        # Interface
        "welcome": "👋 Hi, {name}!\n\nI'm a bot-chef. Tell me your ingredients, and I'll tell you what to cook.",
        "start_manual": "💬 **Send a voice or text message** with your ingredients.\n📝 Or write **\"Give me a recipe for [dish]\"**.",
        "processing": "⏳ Thinking...",
        "menu": "🍴 **What should we cook?**",
        "choose_language": "🌐 **Choose Language:**",
        
        # Categories
        "soup": "🍜 Soups",
        "main": "🥩 Main Courses",
        "salad": "🥗 Salads",
        "breakfast": "🥞 Breakfasts",
        "dessert": "🍰 Desserts",
        "drink": "🍹 Drinks",
        "snack": "🥨 Snacks",
        
        # Buttons
        "btn_favorites": "⭐️ Favorites",
        "btn_restart": "🔄 Restart",
        "btn_change_lang": "🌐 Change Language",
        "btn_help": "❓ Help",
        "btn_add_to_fav": "➕ Add to Favorites",
        "btn_remove_from_fav": "✅ In Favorites",
        "btn_back": "⬅️ Back",
        "btn_another": "➡️ Another Recipe",
        "btn_buy_premium": "💎 Premium",
        "btn_page": "Page {page}/{total}",

        # Recipes and Dishes
        "choose_category": "📝 **Select a dish category:**",
        "choose_dish": "🍳 **Select a dish:**",
        "recipe_title": "✨ **Recipe: {dish_name}**",
        "recipe_ingredients": "🛒 **Ingredients:**",
        "recipe_instructions": "📝 **Instructions:**",
        "recipe_error": "❌ Could not generate a recipe. Please try again or select another dish.",
        "dish_list_error": "❌ Could not get a list of dishes. Please try again or change your ingredients.",
        "error_session_expired": "Session time expired. Please start over by sending a list of ingredients.",

        # Favorites
        "favorites_title": "⭐️ **Your Favorite Recipes**",
        "favorites_empty": "😔 Your favorites list is empty.",
        "favorite_added": "✅ Recipe **{dish_name}** added to favorites!",
        "favorite_removed": "➖ Recipe **{dish_name}** removed from favorites.",
        "favorite_limit": "❌ Favorite recipes limit reached ({limit}).",
        "favorites_list": "⭐️ **Your Favorite Recipes** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (from {date})\n",


        # Errors and Limits
        "limit_voice_exceeded": "❌ **Voice Request Limit Exceeded!**\n\nYou have used {used} of {limit} voice requests today. Limits refresh daily at 00:00.\n\n💎 **Want more?** Use the /stats command",
        "limit_text_exceeded": "❌ **Text Request Limit Exceeded!**\n\nYou have used {used} of {limit} text requests today. Limits refresh daily at 00:00.\n\n💎 **Want more?** Use the /stats command",
        "error_voice_recognition": "🗣️ **Voice recognition error.** Please try speaking clearer or use text input.",
        "error_generation": "❌ An error occurred. Please try again.",
        "error_unknown": "❌ An unknown error occurred.",
        "error_not_enough_products": "🤔 I can't figure out what to cook. Please name more ingredients.",
        "voice_recognized": "✅ Recognized: {text}", # <-- ИСПРАВЛЕНО
        
        # Language
        "lang_changed": "🌐 Language successfully changed to English.",
        "lang_ru": "🇷🇺 Russian",
        "lang_en": "🇬🇧 English",
        "lang_de": "🇩🇪 Deutsch",
        "lang_fr": "🇫🇷 Français",
        "lang_it": "🇮🇹 Italiano",
        "lang_es": "🇪🇸 Español",
        
        # Help
        "help_title": "❓ **Bot Chef Help**",
        "help_text": """
*How to use:*
1. Send ingredients (text or voice)
2. Choose a dish category
3. Choose a dish from the list
4. Get the recipe

*Commands:*
/start - start over
/favorites - favorite recipes
/lang - change language
/help - help
/stats - statistics and limits

*Tips:*
- You can add ingredients multiple times
- Click the ✅ under the recipe to save
- Voice messages are automatically deleted

*Support:* @support
        """,

        "thanks": "😊 You're welcome! 🍽️",
        "easter_egg": "🥚 You found an Easter Egg!",
        "safety_refusal": "🚫 Sorry, I only cook food. I can offer recipes from different world cuisines! 🌍",
    },
    
    # --- НАЧАЛО ЗАГЛУШЕК ---
    "de": {
        "welcome": "👋 Hallo, {name}!\n\nIch bin ein Bot-Koch. Nennen Sie mir Ihre Zutaten, und ich sage Ihnen, was Sie kochen können.",
        "start_manual": "💬 **Senden Sie eine Sprach- oder Textnachricht** mit Ihren Zutaten.\n📝 Oder schreiben Sie **\"Gib mir ein Rezept für [Gericht]\"**.",
        "processing": "⏳ Ich denke nach...",
        "choose_language": "🌐 **Sprache wählen:**",
        "lang_changed": "🌐 Sprache erfolgreich auf Deutsch geändert.",
        "help_title": "❓ **Bot Koch Hilfe**",
        "help_text": "Wie benutzt man...\n",
        "thanks": "😊 Gern geschehen! 🍽️",
        "limit_text_exceeded": "❌ **Textanfrage-Limit überschritten!**\n\nSie haben {used} von {limit} Textanfragen heute verwendet. Limits werden täglich um 00:00 Uhr erneuert.\n\n💎 **Möchten Sie mehr?** Verwenden Sie den Befehl /stats",
        "limit_voice_exceeded": "❌ **Sprachanfrage-Limit überschritten!**\n\nSie haben {used} von {limit} Sprachanfragen heute verwendet. Limits werden täglich um 00:00 Uhr erneuert.\n\n💎 **Möchten Sie mehr?** Verwenden Sie den Befehl /stats",
        "error_generation": "❌ Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.",
        "error_not_enough_products": "🤔 Ich kann nicht herausfinden, was ich kochen soll. Bitte nennen Sie mehr Zutaten.",
        "error_voice_recognition": "🗣️ **Spracherkennungsfehler.** Bitte versuchen Sie, klarer zu sprechen oder verwenden Sie Texteingabe.",
        "voice_recognized": "✅ Erkannt: {text}", # <-- ИСПРАВЛЕНО
        "soup": "🍜 Suppen",
        "main": "🥩 Hauptgerichte",
        "salad": "🥗 Salate",
        "breakfast": "🥞 Frühstücke",
        "dessert": "🍰 Desserts",
        "drink": "🍹 Getränke",
        "snack": "🥨 Snacks",
        "safety_refusal": "🚫 Entschuldigung, ich koche nur Essen. Ich kann Rezepte aus verschiedenen Küchen der Welt anbieten! 🌍",
        "btn_favorites": "⭐️ Favoriten",
        "btn_restart": "🔄 Neustart",
        "btn_change_lang": "🌐 Sprache ändern",
        "btn_help": "❓ Hilfe",
        "favorites_empty": "😔 Favoritenliste ist leer.",
        "favorites_list": "⭐️ **Ihre Lieblingsrezepte** (Seite {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (vom {date})\n",
        "btn_back": "⬅️ Zurück",
        "btn_another": "➡️ Ein anderes Rezept",
        "choose_category": "📝 **Wählen Sie eine Gerichtkategorie:**",
        "choose_dish": "🍳 **Wählen Sie ein Gericht:**",
    },
    
    "fr": {
        "welcome": "👋 Salut, {name}!\n\nJe suis un robot-chef. Dites-moi vos ingrédients, et je vous dirai quoi cuisiner.",
        "start_manual": "💬 **Envoyez un message vocal ou textuel** avec vos ingrédients.\n📝 Ou écrivez **\"Donne-moi une recette de [plat]\"**.",
        "processing": "⏳ Je réfléchis...",
        "choose_language": "🌐 **Choisissez la langue :**",
        "lang_changed": "🌐 Langue changée en français avec succès.",
        "help_title": "❓ **Aide du Bot Chef**",
        "help_text": "Comment utiliser...\n",
        "thanks": "😊 De rien! 🍽️",
        "limit_text_exceeded": "❌ **Limite de requêtes textuelles dépassée!**\n\nVous avez utilisé {used} sur {limit} requêtes textuelles aujourd'hui. Les limites sont renouvelées tous les jours à 00h00.\n\n💎 **Vous voulez plus ?** Utilisez la commande /stats",
        "limit_voice_exceeded": "❌ **Limite de requêtes vocales dépassée!**\n\nVous avez utilisé {used} sur {limit} requêtes vocales aujourd'hui. Les limites sont renouvelées tous les jours à 00h00.\n\n💎 **Vous voulez plus ?** Utilisez la commande /stats",
        "error_generation": "❌ Une erreur s'est produite. Veuillez réessayer.",
        "error_not_enough_products": "🤔 Je n'arrive pas à trouver quoi cuisiner. Veuillez nommer plus d'ingrédients.",
        "error_voice_recognition": "🗣️ **Erreur de reconnaissance vocale.** Veuillez essayer de parler plus clairement ou utiliser la saisie de texte.",
        "voice_recognized": "✅ Reconnu : {text}", # <-- ИСПРАВЛЕНО
        "soup": "🍜 Soupes",
        "main": "🥩 Plats principaux",
        "salad": "🥗 Salades",
        "breakfast": "🥞 Petits déjeuners",
        "dessert": "🍰 Desserts",
        "drink": "🍹 Boissons",
        "snack": "🥨 Snacks",
        "safety_refusal": "🚫 Désolé, je ne cuisine que de la nourriture. Je peux proposer des recettes de différentes cuisines du monde ! 🌍",
        "btn_favorites": "⭐️ Favoris",
        "btn_restart": "🔄 Redémarrer",
        "btn_change_lang": "🌐 Changer de langue",
        "btn_help": "❓ Aide",
        "favorites_empty": "😔 La liste des favoris est vide.",
        "favorites_list": "⭐️ **Vos recettes favorites** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {plat} (du {date})\n",
        "btn_back": "⬅️ Retour",
        "btn_another": "➡️ Une autre recette",
        "choose_category": "📝 **Sélectionnez une catégorie de plat :**",
        "choose_dish": "🍳 **Sélectionnez un plat :**",
    },
    
    "it": {
        "welcome": "👋 Ciao, {name}!\n\nSono un bot-chef. Dimmi i tuoi ingredienti e ti dirò cosa cucinare.",
        "start_manual": "💬 **Invia un messaggio vocale o di testo** con i tuoi ingredienti.\n📝 Oppure scrivi **\"Dammi una ricetta per [piatto]\"**.",
        "processing": "⏳ Sto pensando...",
        "choose_language": "🌐 **Scegli la lingua:**",
        "lang_changed": "🌐 Lingua cambiata in italiano con successo.",
        "help_title": "❓ **Aiuto Bot Chef**",
        "help_text": "Come si usa...\n",
        "thanks": "😊 Prego! 🍽️",
        "limit_text_exceeded": "❌ **Limite richieste di testo superato!**\n\nHai utilizzato {used} su {limit} richieste di testo oggi. I limiti si aggiornano ogni giorno alle 00:00.\n\n💎 **Vuoi di più?** Usa il comando /stats",
        "limit_voice_exceeded": "❌ **Limite richieste vocali superato!**\n\nHai utilizzato {used} su {limit} richieste vocali oggi. I limiti si aggiornano ogni giorno alle 00:00.\n\n💎 **Vuoi di più?** Usa il comando /stats",
        "error_generation": "❌ Si è verificato un errore. Per favore, riprova.",
        "error_not_enough_products": "🤔 Non riesco a capire cosa cucinare. Per favore, nomina più ingredienti.",
        "error_voice_recognition": "🗣️ **Errore di riconoscimento vocale.** Per favore, prova a parlare più chiaramente o usa l'input di testo.",
        "voice_recognized": "✅ Riconosciuto: {text}", # <-- ИСПРАВЛЕНО
        "soup": "🍜 Zuppe",
        "main": "🥩 Secondi piatti",
        "salad": "🥗 Insalate",
        "breakfast": "🥞 Colazioni",
        "dessert": "🍰 Dessert",
        "drink": "🍹 Bevande",
        "snack": "🥨 Stuzzichini",
        "safety_refusal": "🚫 Mi dispiace, cucino solo cibo. Posso offrire ricette da diverse cucine del mondo! 🌍",
        "btn_favorites": "⭐️ Preferiti",
        "btn_restart": "🔄 Riavvia",
        "btn_change_lang": "🌐 Cambia lingua",
        "btn_help": "❓ Aiuto",
        "favorites_empty": "😔 L'elenco dei preferiti è vuoto.",
        "favorites_list": "⭐️ **Le tue ricette preferite** (pagina {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {piatto} (dal {date})\n",
        "btn_back": "⬅️ Indietro",
        "btn_another": "➡️ Un'altra ricetta",
        "choose_category": "📝 **Seleziona una categoria di piatto:**",
        "choose_dish": "🍳 **Seleziona un piatto:**",
    },
    
    "es": {
        "welcome": "👋 Hola, {name}!\n\nSoy un bot-chef. Dime tus ingredientes y te diré qué cocinar.",
        "start_manual": "💬 **Envía un mensaje de voz o texto** con tus ingredientes.\n📝 O escribe **\"Dame una receta de [plato]\"**.",
        "processing": "⏳ Pensando...",
        "menu": "🍴 **¿Qué cocinamos?**",
        "choose_language": "🌐 **Selecciona tu idioma:**",
        "lang_changed": "🌐 Idioma cambiado a español.",
        "help_title": "❓ **Ayuda del Bot Chef**",
        "help_text": "Cómo usar...\n",
        "thanks": "😊 ¡De nada! 🍽️",
        "limit_text_exceeded": "❌ **Límite de solicitudes de texto superado!**\n\nHas usado {used} de {limit} solicitudes de texto hoy. Los límites se actualizan diariamente a las 00:00.\n\n💎 **¿Quieres más?** Usa el comando /stats",
        "limit_voice_exceeded": "❌ **Límite de solicitudes de voz superado!**\n\nHas usado {used} de {limit} solicitudes de voz hoy. Los límites se actualizan diariamente a las 00:00.\n\n💎 **¿Quieres más?** Usa el comando /stats",
        "error_generation": "❌ Ocurrió un error. Por favor, inténtalo de nuevo.",
        "error_not_enough_products": "🤔 No puedo entender qué cocinar. Por favor, nombra más ingredientes.",
        "error_voice_recognition": "🗣️ **Error de reconocimiento de voz.** Intenta hablar más claro o usa la entrada de texto.",
        "voice_recognized": "✅ Reconocido: {text}", # <-- ИСПРАВЛЕНО
        "soup": "🍜 Sopas",
        "main": "🥩 Platos principales",
        "salad": "🥗 Ensaladas",
        "breakfast": "🥞 Desayunos",
        "dessert": "🍰 Postres",
        "drink": "🍹 Bebidas",
        "snack": "🥨 Snacks",
        "safety_refusal": "🚫 Lo siento, solo cocino comida. Puedo ofrecer recetas de diferentes cocinas del mundo! 🌍",
        "btn_favorites": "⭐️ Favoritos",
        "btn_restart": "🔄 Reiniciar",
        "btn_change_lang": "🌐 Cambiar idioma",
        "btn_help": "❓ Ayuda",
        "favorites_empty": "😔 Tu lista de favoritos está vacía.",
        "favorites_list": "⭐️ **Tus Recetas Favoritas** (pág. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {plato} (del {date})\n",
        "btn_back": "⬅️ Atrás",
        "btn_another": "➡️ Otra Receta",
        "choose_category": "📝 **Selecciona una categoría de plato:**",
        "choose_dish": "🍳 **Selecciona un plato:**",
    }
}


def get_text(lang: str, key: str, **kwargs) -> str:
    """Получает текст на нужном языке с подстановкой переменных"""
    # Если язык не поддерживается, используем русский как fallback
    if lang not in TEXTS:
        lang = "ru"
    
    lang_dict = TEXTS.get(lang, TEXTS["ru"])
    # Фолбэк: Текущий язык -> Русский язык -> Пустая строка
    text = lang_dict.get(key, TEXTS["ru"].get(key, ""))
    
    # Подставляем переменные, если они есть
    if kwargs and text:
        try:
            # Используем .format() для подстановки
            return text.format(**kwargs)
        except KeyError:
            # Логируем ошибку, если переменная не найдена в тексте
            logger.warning(f"Переменная не найдена в тексте (lang={lang}, key={key}): {kwargs}")
            return text
    
    return text