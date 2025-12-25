from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# --- ОПИСАНИЯ ПРЕМИУМА ---
PREMIUM_DESC_RU = """💎 **Преимущества Premium:**

✅ **Избранное:** Безлимитное сохранение
✅ **Здоровье:** Расчет КБЖУ для блюд
✅ **Лимиты:** 100 текст / 50 голос (в день)
✅ **Ингредиенты:** До 50 в запросе
✅ **Поддержка:** Приоритетная помощь

👇 **Выберите тариф:**"""

PREMIUM_DESC_EN = """💎 **Premium Benefits:**

✅ **Favorites:** Unlimited saving
✅ **Health:** Nutrition facts (Calories/Macros)
✅ **Limits:** 100 text / 50 voice (daily)
✅ **Ingredients:** Up to 50 per request
✅ **Support:** Priority support

👇 **Choose a plan:**"""

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
        "favorite_added": "⭐ Рецепт **{dish_name}** добавлен!",
        "favorite_removed": "🗑 Рецепт **{dish_name}** удален.",
        "favorite_limit": "❌ Достигнут лимит избранных рецептов ({limit}).",
        "favorites_list": "⭐️ **Ваши избранные рецепты** (стр. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (от {date})\n",
        
        "premium_required_title": "💎 **Требуется Премиум**",
        "premium_required_text": "Функция **Избранное** доступна в полном объеме для Премиум-пользователей.",
        "premium_description": PREMIUM_DESC_RU,

        # НОВЫЕ ТЕКСТЫ
        "limit_favorites_exceeded": "🔒 **Лимит избранного исчерпан!**\n\nВ бесплатной версии можно хранить только 3 рецепта. Купите Премиум для безлимита и КБЖУ.",
        "welcome_gift_alert": "🎁 **Подарок для новых друзей!**\n\nПользуйтесь ботом, а через 48 часов я автоматически подарю вам **7 дней Премиума**, чтобы вы оценили КБЖУ и безлимит. Ждите уведомления! 😉",
        "trial_activated_notification": "🎁 **Ваш подарок активирован!**\n\nВам начислено 7 дней Премиума.\nТеперь доступны:\n✅ Расчет КБЖУ\n✅ Безлимитное Избранное\n✅ 50 голосовых запросов\n\nПопробуйте приготовить что-то особенное!",

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
        "favorite_added": "⭐ Saved!", "favorite_removed": "🗑 Removed.",
        "favorite_limit": "❌ Limit reached ({limit}).",
        "favorites_list": "⭐️ **Favorites** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (from {date})\n",
        
        "premium_required_title": "💎 **Premium Required**",
        "premium_required_text": "Favorites are for Premium users.",
        "premium_description": PREMIUM_DESC_EN,
        
        "limit_favorites_exceeded": "🔒 **Favorites limit reached!**\n\nFree version allows 3 recipes. Get Premium for unlimited storage and Nutrition facts.",
        "welcome_gift_alert": "🎁 **A Gift for New Friends!**\n\nUse the bot, and in 48 hours I'll gift you **7 Days of Premium** to try Nutrition facts and unlimited access. Stay tuned! 😉",
        "trial_activated_notification": "🎁 **Your Gift is Active!**\n\nYou've got 7 Days of Premium.\nNow available:\n✅ Nutrition Facts\n✅ Unlimited Favorites\n✅ 50 Voice requests\n\nTry cooking something special!",
        
        "limit_voice_exceeded": "❌ **Voice limit exceeded!**", "limit_text_exceeded": "❌ **Text limit exceeded!**",
        "error_voice_recognition": "🗣️ **Voice error.**", "error_generation": "❌ Error.", "error_unknown": "❌ Error.", "error_not_enough_products": "🤔 Need ingredients.",
        "voice_recognized": "✅ Recognized: {text}", "lang_changed": "🌐 Language changed.", "safety_refusal": "🚫 Food only.", "help_title": "❓ **Help**", "help_text": "Send ingredients.", "bot_description": "...", "bot_short_description": "...", "thanks": "😊", "easter_egg": "🥚",
    },
    
    "de": {}, "fr": {}, "it": {}, "es": {}
}

# Заполнение заглушек для DE, FR, IT, ES английским текстом (чтобы не было пустоты)
for lang in ["de", "fr", "it", "es"]:
    if not TEXTS[lang]:
        TEXTS[lang] = TEXTS["en"].copy()
        for l_key in ["lang_ru", "lang_en", "lang_de", "lang_fr", "lang_it", "lang_es"]:
             TEXTS[lang][l_key] = TEXTS["en"][l_key]

def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in TEXTS: lang = "ru"
    lang_dict = TEXTS.get(lang, TEXTS["ru"])
    text = lang_dict.get(key, TEXTS["ru"].get(key, ""))
    if kwargs and text:
        try: return text.format(**kwargs)
        except KeyError: 
            # logger.warning(f"Key error in text: {key}")
            return text
    return text