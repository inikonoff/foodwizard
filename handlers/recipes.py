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
    try: await metrics.track_event(user_id, event_name, data)
    except: pass

def safe_format_recipe_text(text: str) -> str:
    if not text: return ""
    # Очищаем заголовки, чтобы они красиво отображались в HTML
    text = text.replace("**", "") # Удаляем Markdown звездочки, так как мы используем parse_mode="HTML" в answer
    text = html.quote(text)
    return text

def parse_direct_request(text: str) -> str | None:
    # (Список триггеров оставим прежним, он хорош)
    triggers = ["recipe ", "recipe for ", "give me ", "make ", "cook ", "how to cook ", "i want "]
    text = text.lower().strip()
    for t in triggers:
        if text.startswith(t): return text[len(t):].strip().rstrip('.?!')
    return None

async def handle_text_message(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # 1. Сразу отвечаем (Debug: Проверить, что бот вообще видит текст)
    # Если здесь будет тишина, значит хендлер не сработал.
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    allowed, used, limit = await users_repo.check_and_increment_request(user_id, "text")
    if not allowed:
        await message.answer(get_text(lang, "limit_text_exceeded"), parse_mode="HTML")
        return

    # Прямой запрос
    direct_dish = parse_direct_request(text)
    if direct_dish:
        state_manager.set_products(user_id, "") 
        # (Импортируем generate_and_send_recipe если он тут не определен или выше)
        await generate_and_send_recipe(message, user_id, direct_dish, "", lang, is_direct=True)
        return

    state_manager.set_products(user_id, text)
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    try:
        # Анализ
        analysis = await groq_service.analyze_products(text, lang, user_id)
        await wait_msg.delete()
        
        if not analysis or not analysis.get("categories"):
            await message.answer(get_text(lang, "error_not_enough_products"))
            return
        
        categories = analysis["categories"]
        suggestion = analysis.get("suggestion")
        
        state_manager.set_categories(user_id, categories)
        if suggestion: await message.answer(suggestion)
            
        builder = InlineKeyboardBuilder()
        valid_cats_count = 0
        for cat in categories:
            # Ищем перевод. Если ключ (напр. 'main') есть в словаре texts.py
            # Кнопка создается.
            label = get_text(lang, cat)
            if label:
                builder.row(InlineKeyboardButton(text=label, callback_data=f"cat_{cat}"))
                valid_cats_count += 1
            else:
                logger.warning(f"Category key '{cat}' missing in translations!")
                
        if valid_cats_count == 0:
            await message.answer("Error: Groq returned unknown categories.")
            return

        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
        
        # Исправление заголовка: удаляем звездочки
        header = get_text(lang, "choose_category").replace("**", "")
        await message.answer(f"<b>{header}</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Text error: {e}", exc_info=True)
        await message.answer(get_text(lang, "error_generation"))

# (Остальной код generate_and_send_recipe и т.д. можно оставить из предыдущих версий, главное применить safe_format и импорты)

async def handle_text_message(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en') # Default EN
    
    if not await users_repo.check_and_increment_request(user_id, "text")[0]:
        await message.answer(get_text(lang, "limit_text_exceeded"), parse_mode="HTML")
        return

    # 1. ПРЯМОЙ ЗАПРОС?
    direct_dish = parse_direct_request(text)
    
    if direct_dish:
        # Это команда! "Boeuf bourguignon"
        state_manager.set_products(user_id, "") 
        await generate_and_send_recipe(message, user_id, direct_dish, "", lang, is_direct=True)
        return

    # 2. СПИСОК ПРОДУКТОВ (если не сработало выше)
    state_manager.set_products(user_id, text)
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    try:
        analysis_result = await groq_service.analyze_products(text, lang, user_id)
        await wait_msg.delete()
        
        if not analysis_result or not analysis_result.get("categories"):
            await track_safely(user_id, "category_analysis_failed", {"products": text})
            await message.answer(get_text(lang, "error_not_enough_products"))
            return
        
        categories = analysis_result["categories"]
        suggestion = analysis_result.get("suggestion")
        state_manager.set_categories(user_id, categories)
        
        if suggestion:
            await message.answer(suggestion)
            
        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.row(InlineKeyboardButton(text=get_text(lang, category), callback_data=f"cat_{category}"))
        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
        await message.answer(get_text(lang, "choose_category"), reply_markup=builder.as_markup())
    except: await message.answer(get_text(lang, "error_generation"))

async def handle_category_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    category = callback.data.split('_')[1]
    products = state_manager.get_products(user_id)
    if not products and products != "":
        await callback.message.edit_text(get_text(lang, "start_manual"))
        return
    wait_msg = await callback.message.edit_text(get_text(lang, "processing"))
    try:
        dishes = await groq_service.generate_dishes_list(products, category, lang)
        await wait_msg.delete()
        if not dishes:
            await callback.message.answer(get_text(lang, "error_generation"))
            return
        state_manager.set_generated_dishes(user_id, dishes)
        builder = InlineKeyboardBuilder()
        for i, dish in enumerate(dishes):
            builder.row(InlineKeyboardButton(text=f"{dish.get('name')}", callback_data=f"dish_{i}"))
        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="back_to_categories"))
        await callback.message.answer(get_text(lang, "choose_dish"), reply_markup=builder.as_markup())
    except: await callback.message.answer(get_text(lang, "error_generation"))

async def handle_dish_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    try:
        dish_index = int(callback.data.split('_')[1])
        dishes = state_manager.get_generated_dishes(user_id)
        if not dishes or dish_index >= len(dishes):
            await callback.message.edit_text(get_text(lang, "error_session_expired"))
            return
        dish = dishes[dish_index]
        state_manager.set_current_dish(user_id, dish)
        await callback.answer()
        
        await generate_and_send_recipe(
            message_or_callback=callback,
            user_id=user_id,
            dish_name=dish.get('name'),
            products=state_manager.get_products(user_id),
            lang=lang,
            is_direct=False
        )
    except: await callback.message.answer(get_text(lang, "error_generation"))

async def handle_back_to_categories(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    categories = state_manager.get_categories(user_id)
    if not categories:
        await callback.message.edit_text(get_text(lang, "error_session_expired"))
        return
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(InlineKeyboardButton(text=get_text(lang, category), callback_data=f"cat_{category}"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
    await callback.message.edit_text(get_text(lang, "choose_category"), reply_markup=builder.as_markup(), parse_mode="Markdown")

def register_recipe_handlers(dp: Dispatcher):
    dp.message.register(handle_text_message, F.text)
    dp.callback_query.register(handle_category_selection, F.data.startswith("cat_"))
    dp.callback_query.register(handle_dish_selection, F.data.startswith("dish_"))
    dp.callback_query.register(handle_back_to_categories, F.data == "back_to_categories")