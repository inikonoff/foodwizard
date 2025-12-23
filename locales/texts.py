from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

TEXTS: Dict[str, Dict[str, str]] = {
    "ru": {
        # --- НАЗВАНИЯ ЯЗЫКОВ (ДОБАВЛЕНО) ---
        "lang_ru": "🇷🇺 Русский",
        "lang_en": "🇬🇧 English",
        "lang_de": "🇩🇪 Deutsch",
        "lang_fr": "🇫🇷 Français",
        "lang_it": "🇮🇹 Italiano",
        "lang_es": "🇪🇸 Español",

        # Интерфейс
        "welcome": """👋 Здравствуйте.

🎤 Отправьте голосовое или текстовое сообщение с перечнем продуктов, и я подскажу, что из них можно приготовить.

📝 Или напишите "Дай рецепт [блюдо]".""",
        
        "start_manual": "", 
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
        "btn_add_to_fav": "☆ В избранное",
        "btn_remove_from_fav": "🌟 В избранном",
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
        "favorite_added": "⭐ Рецепт **{dish_name}** добавлен в избранное!",
        "favorite_removed": "🗑 Рецепт **{dish_name}** удален из избранного.",
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
        "voice_recognized": "✅ Распознано: {text}",
        
        # Язык
        "lang_changed": "🌐 Язык успешно изменен на русский.",

        # Помощь и описания
        "help_title": "❓ **Помощь**",
        "help_text": "Просто отправьте список продуктов, и я подберу рецепт.",
        "bot_description": "...",
        "bot_short_description": "...",
        "thanks": "😊 Пожалуйста! 🍽️",
        "easter_egg": "🥚 Вы нашли пасхальное яйцо!",
        "safety_refusal": "🚫 Извините, я готовлю только еду. Могу предложить рецепты блюд из разных кухонь мира! 🌍",
    },
    
    "en": {
        # --- LANGUAGE NAMES (ADDED) ---
        "lang_ru": "🇷🇺 Russian",
        "lang_en": "🇬🇧 English",
        "lang_de": "🇩🇪 German",
        "lang_fr": "🇫🇷 French",
        "lang_it": "🇮🇹 Italian",
        "lang_es": "🇪🇸 Spanish",

        "welcome": """👋 Hello.

🎤 Send a voice or text message listing your ingredients, and I'll suggest what you can cook with them.

📝 Or write "Give me a recipe for [dish]".""",
        
        "start_manual": "", 
        "processing": "⏳ Thinking...",
        "menu": "🍴 **What should we cook?**",
        "choose_language": "🌐 **Choose Language:**",
        "soup": "🍜 Soups",
        "main": "🥩 Main Courses",
        "salad": "🥗 Salads",
        "breakfast": "🥞 Breakfasts",
        "dessert": "🍰 Desserts",
        "drink": "🍹 Drinks",
        "snack": "🥨 Snacks",
        "btn_favorites": "⭐️ Favorites",
        "btn_restart": "🔄 Restart",
        "btn_change_lang": "🌐 Change Language",
        "btn_help": "❓ Help",
        "btn_add_to_fav": "☆ Add to Favorites",
        "btn_remove_from_fav": "🌟 In Favorites",
        "btn_back": "⬅️ Back",
        "btn_another": "➡️ Another Recipe",
        "btn_buy_premium": "💎 Premium",
        "btn_page": "Page {page}/{total}",
        "choose_category": "📝 **Select a dish category:**",
        "choose_dish": "🍳 **Select a dish:**",
        "recipe_title": "✨ **Recipe: {dish_name}**",
        "recipe_ingredients": "🛒 **Ingredients:**",
        "recipe_instructions": "📝 **Instructions:**",
        "recipe_error": "❌ Could not generate a recipe. Please try again or select another dish.",
        "dish_list_error": "❌ Could not get a list of dishes. Please try again or change your ingredients.",
        "error_session_expired": "Session time expired. Please start over by sending a list of ingredients.",
        "favorites_title": "⭐️ **Your Favorite Recipes**",
        "favorites_empty": "😔 Your favorites list is empty.",
        "favorite_added": "⭐ Recipe **{dish_name}** added to favorites!",
        "favorite_removed": "🗑 Recipe **{dish_name}** removed from favorites.",
        "favorite_limit": "❌ Favorite recipes limit reached ({limit}).",
        "favorites_list": "⭐️ **Your Favorite Recipes** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (from {date})\n",
        "limit_voice_exceeded": "❌ **Voice Request Limit Exceeded!**\n\nYou have used {used} of {limit} voice requests today. Limits refresh daily at 00:00.\n\n💎 **Want more?** Use the /stats command",
        "limit_text_exceeded": "❌ **Text Request Limit Exceeded!**\n\nYou have used {used} of {limit} text requests today. Limits refresh daily at 00:00.\n\n💎 **Want more?** Use the /stats command",
        "error_voice_recognition": "🗣️ **Voice recognition error.** Please try speaking clearer or use text input.",
        "error_generation": "❌ An error occurred. Please try again.",
        "error_unknown": "❌ An unknown error occurred.",
        "error_not_enough_products": "🤔 I can't figure out what to cook. Please name more ingredients.",
        "voice_recognized": "✅ Recognized: {text}",
        "lang_changed": "🌐 Language successfully changed to English.",
        "help_title": "❓ **Bot Chef Help**",
        "help_text": "...",
        "thanks": "😊 You're welcome! 🍽️",
        "easter_egg": "🥚 You found an Easter Egg!",
        "safety_refusal": "🚫 Sorry, I only cook food. I can offer recipes from different world cuisines! 🌍",
        "bot_description": "...",
        "bot_short_description": "...",
    },
    
    # Заглушки для других языков (используем EN как базу, если нет перевода)
    "de": {}, "fr": {}, "it": {}, "es": {}
}

# Заполняем пустые словари английским контентом, чтобы избежать ошибок
for lang in ["de", "fr", "it", "es"]:
    if not TEXTS[lang]:
        TEXTS[lang] = TEXTS["en"].copy()
        # Для названий языков лучше использовать "родные" названия из RU или EN словаря,
        # чтобы они отображались корректно в меню
        for l_key in ["lang_ru", "lang_en", "lang_de", "lang_fr", "lang_it", "lang_es"]:
             TEXTS[lang][l_key] = TEXTS["en"][l_key]

def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in TEXTS: lang = "ru"
    lang_dict = TEXTS.get(lang, TEXTS["ru"])
    text = lang_dict.get(key, TEXTS["ru"].get(key, ""))
    if kwargs and text:
        try: return text.format(**kwargs)
        except KeyError: 
            logger.warning(f"Key error in text: {key}")
            return text
    return text