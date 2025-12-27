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
    except: 
        pass

def safe_format_recipe_text(text: str) -> str:
    """Cleans and formats recipe text for HTML."""
    if not text: 
        return ""
    text = html.quote(text)
    # Convert headers and bold text from Markdown to HTML
    text = re.sub(r'#{1,6}\s*(.*?)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text, flags=re.DOTALL)
    text = re.sub(r'^\s*[\-\*]\s+', r'• ', text, flags=re.MULTILINE)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text, flags=re.DOTALL)
    return text

def parse_direct_request(text: str) -> str | None:
    """
    Проверяет триггеры на всех языках и извлекает название блюда.
    """
    triggers = [
        # ENGLISH
        "recipe ", "recipe for ", "give me ", "make ", "cook ", "how to cook ", "i want ",
        
        # GERMAN
        "rezept ", "rezept für ", "gib mir ein rezept für ", "gib mir ", 
        "koche ", "wie kocht man ", "ich will ",
        
        # FRENCH
        "recette ", "recette de ", "donne-moi une recette de ", "donne-moi ", 
        "cuisine ", "comment faire ", "je veux ", 
        
        # ITALIAN
        "ricetta ", "ricetta di ", "dammi una ricetta per ", "dammi ", 
        "cucina ", "come fare ", "voglio ",
        
        # SPANISH
        "receta ", "receta de ", "dame una receta de ", "dame ", 
        "cocina ", "como hacer ", "quiero ", "dame una "
    ]
    
    # Нормализуем текст (удаляем лишние пробелы, приводим к нижнему регистру)
    # Удаляем знаки препинания в начале (например, если сказали ", дай рецепт")
    lower_text = text.lower().strip().lstrip('.,!? ')
    
    for trigger in triggers:
        trigger = trigger.strip()
        
        # Проверяем вхождение триггера В НАЧАЛЕ фразы
        # Сначала пробуем точное совпадение с пробелом "recipe pizza"
        if lower_text.startswith(trigger + " "):
            return text[len(trigger)+1:].strip().rstrip('.?!')
        
        # Затем пробуем без пробела, если это слово целиком "recipe:"
        if lower_text.startswith(trigger):
            return text[len(trigger):].strip().rstrip('.?!')
            
    return None


async def generate_and_send_recipe(message_or_callback, user_id, dish_name, products, lang, is_direct=False):
    try:
        user_data = await users_repo.get_user(user_id)
        is_premium = user_data.get('is_premium', False)
        
        msg_obj = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
        
        if isinstance(message_or_callback, Message): 
            wait_msg = await msg_obj.answer(get_text(lang, "processing"))
        else: 
            wait_msg = await msg_obj.edit_text(get_text(lang, "processing"))
            
        recipe = await groq_service.generate_recipe(dish_name, products, lang, user_id, is_premium, is_direct)
        await wait_msg.delete()

        # ✅ FIXED: Check if recipe is empty
        if not recipe or not recipe.strip():
            logger.warning(f"Empty recipe received for dish: {dish_name}")
            error_msg = get_text(lang, "error_generation")
            if not error_msg or not error_msg.strip():
                error_msg = "Failed to generate recipe. Please try again."
            await msg_obj.answer(error_msg)
            return

        # ✅ FIXED: Check for safety refusal (with null check)
        safety_text = get_text(lang, "safety_refusal")
        if safety_text and safety_text in recipe:
            await msg_obj.answer(safety_text)
            return

        final_recipe_text = safe_format_recipe_text(recipe)
        state_manager.set_current_recipe_text(user_id, final_recipe_text)

        await track_safely(user_id, "recipe_generated", {"dish": dish_name, "direct": is_direct})
        
        # Prepare data for buttons
        if is_direct:
            fake_dishes = [{"name": dish_name, "category": "direct"}]
            state_manager.set_generated_dishes(user_id, fake_dishes)
            state_manager.set_current_dish(user_id, fake_dishes[0])
            dish_index = 0
        else:
            dishes = state_manager.get_generated_dishes(user_id) or []
            dish_index = 0
            for i, d in enumerate(dishes):
                if d.get('name') == dish_name:
                    dish_index = i
                    state_manager.set_current_dish(user_id, d)
                    break
        
        is_favorite = await favorites_repo.is_favorite(user_id, dish_name)
        builder = InlineKeyboardBuilder()
        
        # Favorite buttons
        if is_favorite:
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_remove_from_fav"), callback_data=f"remove_fav_{dish_index}"))
        else:
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_add_to_fav"), callback_data=f"add_fav_{dish_index}"))
        
        # Navigation buttons
        if is_direct:
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
        else:
            back_data = "back_to_categories"
            another_cb = message_or_callback.data if isinstance(message_or_callback, CallbackQuery) else "restart"
            builder.row(
                InlineKeyboardButton(text=get_text(lang, "btn_another"), callback_data=another_cb),
                InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data=back_data)
            )
        
        await msg_obj.answer(final_recipe_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Gen error: {e}", exc_info=True)
        try: 
            msg = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
            error_msg = get_text(lang, "error_generation")
            if not error_msg or not error_msg.strip():
                error_msg = "Error generating recipe."
            await msg.answer(error_msg)
        except Exception as inner_e:
            logger.error(f"Could not send error message: {inner_e}")


async def handle_text_message(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Ignore commands
    if text.startswith("/"):
        return

    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    # ✅ FIXED: Correct limit check
    limit_result = await users_repo.check_and_increment_request(user_id, "text")
    if not limit_result[0]:
        await message.answer(get_text(lang, "limit_text_exceeded"), parse_mode="HTML")
        return

    # 1. Direct request
    direct_dish = parse_direct_request(text)
    if direct_dish:
        state_manager.set_products(user_id, "") 
        await generate_and_send_recipe(message, user_id, direct_dish, "", lang, is_direct=True)
        return

    # 2. Product analysis
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
        valid_count = 0
        for category in categories:
            label = get_text(lang, category)
            # Fallback to English if translation missing
            if not label or label.strip() == "":
                label = get_text("en", category)
                if not label: 
                    label = category.title()
            
            builder.row(InlineKeyboardButton(text=label, callback_data=f"cat_{category}"))
            valid_count += 1
                
        if valid_count == 0:
            await message.answer(get_text(lang, "error_generation"))
            return

        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
        
        header = get_text(lang, "choose_category").replace("**", "")
        await message.answer(f"<b>{header}</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        error_msg = get_text(lang, "error_generation")
        if not error_msg or not error_msg.strip():
            error_msg = "Error analyzing ingredients."
        await message.answer(error_msg)


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
            error_msg = get_text(lang, "error_generation")
            await callback.message.answer(error_msg)
            return
        
        state_manager.set_generated_dishes(user_id, dishes)
        builder = InlineKeyboardBuilder()
        for i, dish in enumerate(dishes):
            builder.row(InlineKeyboardButton(text=f"{dish.get('name')}", callback_data=f"dish_{i}"))
        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="back_to_categories"))
        
        # Fixed header (removed asterisks)
        dish_header = get_text(lang, "choose_dish").replace("**", "").format(category=get_text(lang, category) or category)
        await callback.message.answer(dish_header, reply_markup=builder.as_markup())
    except Exception as e:
        logger.error(f"Category selection error: {e}", exc_info=True)
        error_msg = get_text(lang, "error_generation")
        if not error_msg or not error_msg.strip():
            error_msg = "Error loading dishes."
        await callback.message.answer(error_msg)


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
        await generate_and_send_recipe(callback, user_id, dish.get('name'), state_manager.get_products(user_id), lang, is_direct=False)
    except Exception as e:
        logger.error(f"Dish selection error: {e}", exc_info=True)
        error_msg = get_text(lang, "error_generation")
        if not error_msg or not error_msg.strip():
            error_msg = "Error selecting dish."
        await callback.message.answer(error_msg)


async def handle_back_to_categories(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    categories = state_manager.get_categories(user_id)
    if not categories:
        await callback.message.edit_text(get_text(lang, "error_session_expired"))
        return
    builder = InlineKeyboardBuilder()
    for category in categories:
        label = get_text(lang, category)
        if not label: 
            label = category.title()
        builder.row(InlineKeyboardButton(text=label, callback_data=f"cat_{category}"))
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
    
    header = get_text(lang, "choose_category").replace("**", "")
    await callback.message.edit_text(f"<b>{header}</b>", reply_markup=builder.as_markup(), parse_mode="HTML")


def register_recipe_handlers(dp: Dispatcher):
    dp.message.register(handle_text_message, F.text, ~F.text.startswith('/'))
    dp.callback_query.register(handle_category_selection, F.data.startswith("cat_"))
    dp.callback_query.register(handle_dish_selection, F.data.startswith("dish_"))
    dp.callback_query.register(handle_back_to_categories, F.data == "back_to_categories")
