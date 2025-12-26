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
    text = html.quote(text)
    text = re.sub(r'#{1,6}\s*(.*?)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text, flags=re.DOTALL)
    text = re.sub(r'^\s*[\-\*]\s+', r'• ', text, flags=re.MULTILINE)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text, flags=re.DOTALL)
    return text

def parse_direct_request(text: str) -> str | None:
    # EN, DE, FR, IT, ES Triggers
    triggers = ["recipe", "recipe for", "give me", "make", "cook", "how to cook", "i want",
                "rezept", "rezept für", "koch", "koche", "wie kocht man", "ich will",
                "recette", "donne-moi", "donne moi", "donnez-moi", "donnez moi", "cuisine", "cuisiner", "je veux", "comment faire",
                "ricetta", "dammi", "dimmi", "cucina", "cucinare", "voglio", "vorrei", "come fare",
                "receta", "dame", "cocina", "cocinar", "quiero", "como hacer"]
    
    text_clean = text.lower().strip().lstrip(".,!?¡¿- ")
    for trigger in triggers:
        if text_clean.startswith(trigger):
            start = text_clean.find(trigger) + len(trigger)
            rest = text_clean[start:].strip()
            # Clean articles
            junk = r'^(a|an|the|for|of|about|un|une|le|la|les|du|de|des|pour|ein|eine|einen|der|die|das|für|von|el|los|las|para|il|lo|per|di)\s+'
            dish = re.sub(junk, '', rest)
            if dish.startswith("recipe") or dish.startswith("recette"): 
                 dish = dish.split(' ', 1)[1] if ' ' in dish else dish
                 dish = re.sub(junk, '', dish.strip())
            
            if dish and len(dish) > 1: return dish.rstrip('.?!')
    return None

async def generate_and_send_recipe(message_or_callback, user_id, dish_name, products, lang, is_direct=False):
    try:
        user_data = await users_repo.get_user(user_id)
        is_premium = user_data.get('is_premium', False)
        
        msg_obj = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
        
        if isinstance(message_or_callback, Message): wait_msg = await msg_obj.answer(get_text(lang, "processing"))
        else: wait_msg = await msg_obj.edit_text(get_text(lang, "processing"))
            
        recipe = await groq_service.generate_recipe(dish_name, products, lang, user_id, is_premium, is_direct)
        await wait_msg.delete()

        if get_text(lang, "safety_refusal") in recipe:
             await msg_obj.answer(get_text(lang, "safety_refusal"))
             return

        final_recipe_text = safe_format_recipe_text(recipe)
        state_manager.set_current_recipe_text(user_id, final_recipe_text)
        await track_safely(user_id, "recipe_generated", {"dish": dish_name, "direct": is_direct})
        
        if is_direct:
            fake = [{"name": dish_name, "category": "direct"}]
            state_manager.set_generated_dishes(user_id, fake)
            state_manager.set_current_dish(user_id, fake[0])
            dish_index = 0
        else:
             dishes = state_manager.get_generated_dishes(user_id) or []
             dish_index = next((i for i, d in enumerate(dishes) if d.get('name') == dish_name), 0)
        
        is_fav = await favorites_repo.is_favorite(user_id, dish_name)
        b = InlineKeyboardBuilder()
        
        if is_fav: b.row(InlineKeyboardButton(text=get_text(lang, "btn_remove_from_fav"), callback_data=f"remove_fav_{dish_index}"))
        else: b.row(InlineKeyboardButton(text=get_text(lang, "btn_add_to_fav"), callback_data=f"add_fav_{dish_index}"))
        
        if is_direct:
            b.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
        else:
            cb_another = message_or_callback.data if isinstance(message_or_callback, CallbackQuery) else "restart"
            b.row(
                InlineKeyboardButton(text=get_text(lang, "btn_another"), callback_data=cb_another),
                InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="back_to_categories")
            )
        
        await msg_obj.answer(final_recipe_text, reply_markup=b.as_markup(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Gen error: {e}", exc_info=True)
        try: 
            msg = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
            await msg.answer(get_text(lang, "error_generation"))
        except: pass

async def handle_text_message(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    # !!! ИСПРАВЛЕНИЕ: Разбиваем на две строки (безопасная распаковка) !!!
    allowed, used, limit = await users_repo.check_and_increment_request(user_id, "text")
    if not allowed:
        await message.answer(get_text(lang, "limit_text_exceeded"), parse_mode="HTML")
        return

    # ПРЯМОЙ ЗАПРОС
    direct_dish = parse_direct_request(text)
    if direct_dish:
        state_manager.set_products(user_id, "") 
        await generate_and_send_recipe(message, user_id, direct_dish, "", lang, is_direct=True)
        return

    # АНАЛИЗ ПРОДУКТОВ
    state_manager.set_products(user_id, text)
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    try:
        res = await groq_service.analyze_products(text, lang, user_id)
        await wait_msg.delete()
        
        if not res or not res.get("categories"):
            await track_safely(user_id, "category_analysis_failed", {"products": text})
            await message.answer(get_text(lang, "error_not_enough_products"))
            return
        
        cats = res["categories"]
        suggestion = res.get("suggestion")
        
        state_manager.set_categories(user_id, cats)
        if suggestion: await message.answer(suggestion)
            
        b = InlineKeyboardBuilder()
        # Проверяем, есть ли перевод для категорий, чтобы не показывать пустые кнопки
        for cat in cats:
            label = get_text(lang, cat)
            if label:
                b.row(InlineKeyboardButton(text=label, callback_data=f"cat_{cat}"))
                
        b.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
        await message.answer(get_text(lang, "choose_category"), reply_markup=b.as_markup())
        
    except Exception as e:
        logger.error(f"Text error: {e}", exc_info=True)
        await message.answer(get_text(lang, "error_generation"))

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
        b = InlineKeyboardBuilder()
        for i, dish in enumerate(dishes):
            b.row(InlineKeyboardButton(text=f"{dish.get('name')}", callback_data=f"dish_{i}"))
        b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="back_to_categories"))
        await callback.message.answer(get_text(lang, "choose_dish"), reply_markup=b.as_markup())
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
        await generate_and_send_recipe(callback, user_id, dish.get('name'), state_manager.get_products(user_id), lang, is_direct=False)
    except: await callback.message.answer(get_text(lang, "error_generation"))

async def handle_back_to_categories(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    categories = state_manager.get_categories(user_id)
    if not categories:
        await callback.message.edit_text(get_text(lang, "error_session_expired"))
        return
    b = InlineKeyboardBuilder()
    for cat in categories:
        label = get_text(lang, cat)
        if label: b.row(InlineKeyboardButton(text=label, callback_data=f"cat_{cat}"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
    await callback.message.edit_text(get_text(lang, "choose_category"), reply_markup=b.as_markup())

def register_recipe_handlers(dp: Dispatcher):
    dp.message.register(handle_text_message, F.text)
    dp.callback_query.register(handle_category_selection, F.data.startswith("cat_"))
    dp.callback_query.register(handle_dish_selection, F.data.startswith("dish_"))
    dp.callback_query.register(handle_back_to_categories, F.data == "back_to_categories")