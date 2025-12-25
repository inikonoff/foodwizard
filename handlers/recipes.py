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
    triggers = ["recipe ", "recipe for ", "give me ", "make ", "cook ", "how to cook ", "i want ",
                "rezept ", "rezept für ", "koch ", "koche ", "wie kocht man ", "ich will ",
                "recette ", "recette de ", "cuisine ", "cuisiner ", "je veux ", "comment faire ",
                "ricetta ", "ricetta di ", "cucina ", "cucinare ", "voglio ", "come fare ",
                "receta ", "receta de ", "cocina ", "cocinar ", "quiero ", "como hacer "]
    lower_text = text.lower().strip()
    for trigger in triggers:
        trigger = trigger.strip()
        if lower_text.startswith(trigger + " "):
            return text[len(trigger)+1:].strip().rstrip('.?!')
        if lower_text.startswith(trigger):
            return text[len(trigger):].strip().rstrip('.?!')
    return None

# --- ИСПРАВЛЕННАЯ ЛОГИКА СОХРАНЕНИЯ СОСТОЯНИЯ ---
async def generate_and_send_recipe(message_or_callback, user_id, dish_name, products, lang, is_direct=False):
    try:
        user_data = await users_repo.get_user(user_id)
        is_premium = user_data.get('is_premium', False)
        
        msg_obj = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
        
        if isinstance(message_or_callback, Message): wait_msg = await msg_obj.answer(get_text(lang, "processing"))
        else: wait_msg = await msg_obj.edit_text(get_text(lang, "processing"))
            
        recipe = await groq_service.generate_recipe(dish_name, products, lang, user_id, is_premium)
        await wait_msg.delete()

        if get_text(lang, "safety_refusal") in recipe:
             await msg_obj.answer(get_text(lang, "safety_refusal"))
             return

        final_recipe_text = safe_format_recipe_text(recipe)
        state_manager.set_current_recipe_text(user_id, final_recipe_text)
        await track_safely(user_id, "recipe_generated", {"dish": dish_name})
        
        # ХАК ДЛЯ "DISH NOT FOUND": СОЗДАЕМ КОНТЕКСТ ДЛЯ КНОПОК
        if is_direct:
            # Если это прямой запрос, мы должны создать искусственный "список" из 1 блюда в памяти
            fake_dishes = [{"name": dish_name, "category": "direct"}]
            state_manager.set_generated_dishes(user_id, fake_dishes)
            state_manager.set_current_dish(user_id, fake_dishes[0])
            dish_index = 0
        else:
             # Если не прямой, пытаемся найти блюдо в уже существующем списке
             dishes = state_manager.get_generated_dishes(user_id) or []
             # Пытаемся найти по имени
             dish_index = 0
             for i, d in enumerate(dishes):
                 if d.get('name') == dish_name:
                     dish_index = i
                     # Обновляем Current Dish на всякий случай
                     state_manager.set_current_dish(user_id, d)
                     break
        
        # КНОПКИ
        is_favorite = await favorites_repo.is_favorite(user_id, dish_name)
        builder = InlineKeyboardBuilder()
        
        if is_favorite:
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_remove_from_fav"), callback_data=f"remove_fav_{dish_index}"))
        else:
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_add_to_fav"), callback_data=f"add_fav_{dish_index}"))
        
        if is_direct:
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
        else:
            another_cb = message_or_callback.data if isinstance(message_or_callback, CallbackQuery) else "restart"
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_another"), callback_data=another_cb),
                        InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="back_to_categories"))
        
        await msg_obj.answer(final_recipe_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
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
    
    allowed, used, limit = await users_repo.check_and_increment_request(user_id, "text")
    if not allowed:
        await message.answer(get_text(lang, "limit_text_exceeded"), parse_mode="HTML")
        return

    direct_dish = parse_direct_request(text)
    if direct_dish:
        state_manager.set_products(user_id, "") 
        # Прямой запрос
        await generate_and_send_recipe(message, user_id, direct_dish, "", lang, is_direct=True)
        return

    state_manager.set_products(user_id, text)
    wait_msg = await message.answer(get_text(lang, "processing"))
    try:
        categories = await groq_service.analyze_products(text, lang)
        await wait_msg.delete()
        if not categories:
            await message.answer(get_text(lang, "error_not_enough_products"))
            return
        state_manager.set_categories(user_id, categories)
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
        state_manager.set_current_dish(user_id, dish) # ВАЖНО: Устанавливаем здесь
        await callback.answer()
        
        # Вызываем общую функцию (не is_direct)
        await generate_and_send_recipe(callback, user_id, dish.get('name'), state_manager.get_products(user_id), lang, is_direct=False)
        
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