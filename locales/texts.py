from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

TEXTS: Dict[str, Dict[str, str]] = {
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
        
        # Кнопки
        "btn_favorites": "⭐️ Избранное",
        "btn_restart": "🔄 Рестарт",
        "btn_change_lang": "🌐 Язык",
        "btn_help": "❓ Помощь",
        "btn_add_to_fav": "☆ В избранное",
        "btn_remove_from_fav": "🌟 В избранном",
        "btn_back": "⬅️ Назад",
        "btn_another": "➡️ Ещё рецепт",
        "btn_buy_premium": "💎 Купить Премиум", # <-- Кнопка в меню
        "btn_page": "Стр. {page}/{total}",
        
        # Рецепты
        "choose_category": "📝 **Выберите категорию блюд:**",
        "choose_dish": "🍳 **Выберите блюдо:**",
        "recipe_title": "✨ **Рецепт: {dish_name}**",
        "recipe_ingredients": "🛒 **Ингредиенты:**",
        "recipe_instructions": "📝 **Инструкция:**",
        "recipe_error": "❌ Не удалось сгенерировать рецепт.",
        "dish_list_error": "❌ Не удалось получить список блюд.",
        "error_session_expired": "Время сессии истекло. Начните заново.",
        
        # Избранное
        "favorites_title": "⭐️ **Ваши избранные рецепты**",
        "favorites_empty": "😔 Список избранного пуст.",
        "favorite_added": "⭐ Рецепт **{dish_name}** добавлен в избранное!",
        "favorite_removed": "🗑 Рецепт **{dish_name}** удален из избранного.",
        "favorite_limit": "❌ Достигнут лимит избранных рецептов ({limit}).",
        "favorites_list": "⭐️ **Ваши избранные рецепты** (стр. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (от {date})\n",
        
        # Премиум и Лимиты
        "premium_required_title": "💎 **Требуется Премиум**",
        "premium_required_text": "Функция **Избранное** доступна только для Премиум-пользователей.\n\nСохраняйте любимые рецепты и увеличьте лимиты!",
        
        "premium_description": """💎 **Преимущества Premium:**

✅ **Избранное:** Сохраняйте любые рецепты
✅ **Текстовые запросы:** 100 в день (вместо 10)
✅ **Голосовые запросы:** 50 в день (вместо 3)
✅ **Ингредиенты:** До 50 в одном запросе
✅ **Поддержка:** Приоритетная помощь

👇 **Выберите тариф:**""",

        "limit_voice_exceeded": "❌ **Лимит голосовых запросов исчерпан!**\n💎 Купите Премиум для увеличения лимитов.",
        "limit_text_exceeded": "❌ **Лимит текстовых запросов исчерпан!**\n💎 Купите Премиум для увеличения лимитов.",
        
        # Ошибки
        "error_voice_recognition": "🗣️ **Ошибка распознавания.**",
        "error_generation": "❌ Произошла ошибка.",
        "error_unknown": "❌ Неизвестная ошибка.",
        "error_not_enough_products": "🤔 Не могу понять, что приготовить. Назовите больше продуктов.",
        "voice_recognized": "✅ Распознано: {text}",
        "lang_changed": "🌐 Язык изменен на Русский.",
        "safety_refusal": "🚫 Извините, я готовлю только еду.",
        "help_title": "❓ **Помощь**",
        "help_text": "Отправьте список продуктов, и я подберу рецепт.",
        "bot_description": "...",
        "bot_short_description": "...",
        "thanks": "😊",
        "easter_egg": "🥚",
    },
    
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
        "btn_buy_premium": "💎 Get Premium", # <-- Кнопка в меню
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
        "premium_required_text": "The **Favorites** feature is available only for Premium users.\n\nSave your recipes and increase limits!",
        
        "premium_description": """💎 **Premium Benefits:**

✅ **Favorites:** Save unlimited recipes
✅ **Text Requests:** 100/day (vs 10)
✅ **Voice Requests:** 50/day (vs 3)
✅ **Ingredients:** Up to 50 per request
✅ **Support:** Priority support

👇 **Choose a plan:**""",

        "limit_voice_exceeded": "❌ **Voice limit exceeded!**\n💎 Get Premium to increase limits.",
        "limit_text_exceeded": "❌ **Text limit exceeded!**\n💎 Get Premium to increase limits.",
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
    
    "de": {}, "fr": {}, "it": {}, "es": {}
}

# Заполняем заглушки английским
for lang in ["de", "fr", "it", "es"]:
    if not TEXTS[lang]:
        TEXTS[lang] = TEXTS["en"].copy()
        # Для корректного отображения списка языков копируем названия
        for l_key in ["lang_ru", "lang_en", "lang_de", "lang_fr", "lang_it", "lang_es"]:
             TEXTS[lang][l_key] = TEXTS["en"][l_key]

def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in TEXTS: lang = "ru"
    lang_dict = TEXTS.get(lang, TEXTS["ru"])
    text = lang_dict.get(key, TEXTS["ru"].get(key, ""))
    if kwargs and text:
        try: return text.format(**kwargs)
        except KeyError: return text
    return text