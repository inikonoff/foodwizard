import logging
import re
from aiogram import Dispatcher, F, html
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from services.groq_service import groq_service
from locales.texts import get_text
from state_manager import state_manager

logger = logging.getLogger(__name__)

async def track_safely(user_id: int, event_name: str, data: dict = None):
    try:
        await metrics.track_event(user_id, event_name, data)
    except Exception as e:
        logger.error(f"❌ Ошибка записи метрики ({event_name}): {e}", exc_info=True)

# Функция очистки Markdown (делает красиво)
def safe_format_recipe_text(text: str) -> str:
    if not text: return ""
    text = html.quote(text)
    text = re.sub(r'#{1,6}\s*(.*?)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text, flags=re.DOTALL)
    text = re.sub(r'^\s*[\-\*]\s+', r'• ', text, flags=re.MULTILINE)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text, flags=re.DOTALL)
    return text

# --- ПАСХАЛКА: ПРОВЕРКА НА ПРЯМОЙ ЗАПРОС ---
def parse_direct_request(text: str) -> str | None:
    """
    Проверяет, является ли сообщение прямым запросом рецепта.
    Возвращает название блюда или None.
    """
    # Ключевые фразы (на русском и английском)
    triggers = [
        "рецепт ", "recipe ", 
        "дай рецепт ", "give recipe ", "give me recipe ",
        "как приготовить ", "how to cook "
    ]
    
    lower_text = text.lower()
    for trigger in triggers:
        if lower_text.startswith(trigger):
            # Возвращаем всё, что идет после триггера (обрезаем пробелы)
            dish_name = text[len(trigger):].strip()
            # Убираем знаки препинания в конце, если есть
            dish_name = dish_name.rstrip('.?!')
            if dish_name:
                return dish_name
    return None

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ГЕНЕРАЦИИ И ОТПРАВКИ ---
async def generate_and_send_recipe(message_or_callback, user_id, dish_name, products, lang, is_direct=False):
    """Единая функция для генерации рецепта (чтобы не дублировать код)"""
    try:
        # Если это прямой запрос (текст), отвечаем, если коллбэк - редактируем
        if isinstance(message_or_callback, Message):
            wait_msg = await message_or_callback.answer(get_text(lang, "processing"))
        else:
            wait_msg = await message_or_callback.message.edit_text(get_text(lang, "processing"))
            
        # Генерируем рецепт
        recipe = await groq_service.generate_recipe(dish_name, products, lang)
        await wait_msg.delete()

        if get_text(lang, "safety_refusal") in recipe:
             msg = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
             await msg.answer(get_text(lang, "safety_refusal"))
             return

        final_recipe_text = safe_format_recipe_text(recipe)
        state_manager.set_current_recipe_text(user_id, final_recipe_text)

        await track_safely(user_id, "recipe_generated", {
            "dish_name": dish_name, 
            "language": lang, 
            "type": "direct" if is_direct else "selection"
        })
        
        # Кнопки
        # Поскольку у нас нет dish_index (для прямого запроса), используем 0 или спец. ID
        # Но чтобы кнопки работали, нужно, чтобы dish был в generated_dishes
        # ХАК: Добавляем этот "прямой" рецепт в список generated_dishes как единственный элемент
        fake_dish_obj = {"name": dish_name, "category": "direct_request"}
        state_manager.set_generated_dishes(user_id, [fake_dish_obj])
        state_manager.set_current_dish(user_id, fake_dish_obj)
        dish_index = 0 

        is_favorite = await favorites_repo.is_favorite(user_id, dish_name)
        builder = InlineKeyboardBuilder()
        
        if is_favorite:
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_remove_from_fav"), callback_data=f"remove_fav_{dish_index}"))
        else:
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_add_to_fav"), callback_data=f"add_fav_{dish_index}"))
        
        # Кнопку "Еще рецепт" скрываем или меняем на "Рестарт" для прямых запросов
        if is_direct:
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
        else:
            # Для коллбэка (из списка) нужна кнопка назад
            back_data = "back_to_categories"
            if isinstance(message_or_callback, CallbackQuery):
                back_data = "back_to_categories"
            builder.row(
                InlineKeyboardButton(text=get_text(lang, "btn_another"), callback_data=message_or_callback.data if isinstance(message_or_callback, CallbackQuery) else "restart"),
                InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data=back_data)
            )
        
        msg_target = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
        await msg_target.answer(final_recipe_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации рецепта: {e}", exc_info=True)
        try: await wait_msg.delete() 
        except: pass
        msg_target = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
        await msg_target.answer(get_text(lang, "error_generation"))


async def handle_text_message(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    allowed, used, limit = await users_repo.check_and_increment_request(user_id, "text")
    if not allowed:
        await message.answer(get_text(lang, "limit_text_exceeded", used=used, limit=limit), parse_mode="HTML")
        return

    # --- ПРОВЕРКА НА ПАСХАЛКУ (ПРЯМОЙ ЗАПРОС) ---
    direct_dish_name = parse_direct_request(text)
    
    if direct_dish_name:
        # Если это прямой запрос (например, "Рецепт борща")
        # Мы считаем, что продуктов у пользователя нет (или они подразумеваются)
        # Поэтому передаем пустую строку продуктов, чтобы бот написал "купить" для всего
        # Или можно передать сам текст запроса как контекст.
        
        # Сохраняем состояние
        state_manager.set_products(user_id, "") # Продукты неизвестны
        
        await generate_and_send_recipe(
            message_or_callback=message,
            user_id=user_id,
            dish_name=direct_dish_name,
            products="", # Пустые продукты -> бот предложит всё купить (что логично)
            lang=lang,
            is_direct=True
        )
        return

    # --- ОБЫЧНЫЙ ФЛОУ (АНАЛИЗ ПРОДУКТОВ) ---
    state_manager.set_products(user_id, text)
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    try:
        categories = await groq_service.analyze_products(text, lang)
        await wait_msg.delete()
        
        if not categories:
            await track_safely(user_id, "category_analysis_failed", {"language": lang, "products": text})
            await message.answer(get_text(lang, "error_not_enough_products"))
            return
        
        state_manager.set_categories(user_id, categories)
        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.row(InlineKeyboardButton(text=get_text(lang, category), callback_data=f"cat_{category}"))
        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
        
        await message.answer(get_text(lang, "choose_category"), reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"❌ Ошибка анализа категорий (handle_text_message): {e}", exc_info=True)
        await wait_msg.delete()
        await message.answer(get_text(lang, "error_generation"))

async def handle_category_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    category = callback.data.split('_')[1]
    products = state_manager.get_products(user_id)
    
    if not products and products != "": # Пустая строка допустима только при прямом запросе, но тут мы в меню
        await callback.message.edit_text(get_text(lang, "start_manual"))
        await callback.answer()
        return

    wait_msg = await callback.message.edit_text(get_text(lang, "processing"))
    await callback.answer()

    try:
        dishes = await groq_service.generate_dishes_list(products, category, lang)
        await wait_msg.delete()
        
        if not dishes:
            await track_safely(user_id, "dish_list_failed", {"language": lang, "category": category, "products": products})
            await callback.message.answer(get_text(lang, "error_generation"))
            return
        
        state_manager.set_generated_dishes(user_id, dishes)
        builder = InlineKeyboardBuilder()
        for i, dish in enumerate(dishes):
            builder.row(InlineKeyboardButton(text=f"{dish.get('name')}", callback_data=f"dish_{i}"))
        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="back_to_categories"))
        
        await callback.message.answer(get_text(lang, "choose_dish").format(category=get_text(lang, category)), reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации списка блюд: {e}", exc_info=True)
        await wait_msg.delete()
        await callback.message.answer(get_text(lang, "error_generation"))

async def handle_dish_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    
    try:
        dish_index = int(callback.data.split('_')[1])
        dishes = state_manager.get_generated_dishes(user_id)
        
        if not dishes or dish_index >= len(dishes):
            await callback.message.edit_text(get_text(lang, "error_session_expired"))
            await callback.answer()
            return

        dish = dishes[dish_index]
        products = state_manager.get_products(user_id)
        state_manager.set_current_dish(user_id, dish)

        await callback.answer() # Отвечаем сразу, чтобы часики не висели
        
        # Используем общую функцию генерации
        await generate_and_send_recipe(
            message_or_callback=callback,
            user_id=user_id,
            dish_name=dish.get('name'),
            products=products,
            lang=lang,
            is_direct=False
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка выбора блюда: {e}", exc_info=True)
        await callback.message.answer(get_text(lang, "error_generation"))

async def handle_back_to_categories(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    categories = state_manager.get_categories(user_id)
    if not categories:
        await callback.message.edit_text(get_text(lang, "error_session_expired"))
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(InlineKeyboardButton(text=get_text(lang, category), callback_data=f"cat_{category}"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
    await callback.message.edit_text(get_text(lang, "choose_category"), reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

def register_recipe_handlers(dp: Dispatcher):
    dp.message.register(handle_text_message, F.text)
    dp.callback_query.register(handle_category_selection, F.data.startswith("cat_"))
    dp.callback_query.register(handle_dish_selection, F.data.startswith("dish_"))
    dp.callback_query.register(handle_back_to_categories, F.data == "back_to_categories")