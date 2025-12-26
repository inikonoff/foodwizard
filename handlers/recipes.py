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
    # Заголовки (### Заголовок)
    text = re.sub(r'#{1,6}\s*(.*?)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    # Жирный (**text**)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    # Альтернативный жирный (__text__)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text, flags=re.DOTALL)
    # Курсив (*text*) - проверка, чтобы не ломать жирный
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text, flags=re.DOTALL)
    # Списки
    text = re.sub(r'^\s*[\-\*]\s+', r'• ', text, flags=re.MULTILINE)
    # Моноширинный (`code`)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text, flags=re.DOTALL)
    return text

# --- МУЛЬТИЯЗЫЧНАЯ ПРОВЕРКА НА ПРЯМОЙ ЗАПРОС ---
def parse_direct_request(text: str) -> str | None:
    """
    Проверяет, является ли текст командой (на EN, DE, FR, IT, ES).
    Вырезает мусорные слова (артикли, предлоги) и возвращает название блюда.
    """
    text = text.strip()
    lower_text = text.lower()
    
    # Расширенный список триггеров
    triggers = [
        # ENGLISH
        "recipe", "give me", "give", "make", "cook", "how to cook", "i want", "create", "show me",
        # GERMAN
        "rezept", "gib mir", "zeig mir", "koch", "koche", "wie kocht man", "ich will", "zubereiten",
        # FRENCH ("Donne-moi" добавлено!)
        "recette", "donne-moi", "donne moi", "donnez-moi", "donnez moi", "cuisine", "cuisiner", 
        "je veux", "comment faire", "comment cuisiner", "préparer", "faire",
        # ITALIAN
        "ricetta", "dammi", "dimmi", "cucina", "cucinare", "voglio", "vorrei", "come fare", "prepara",
        # SPANISH
        "receta", "dame", "cocina", "cocinar", "quiero", "como hacer", "preparar", "dame una"
    ]
    
    # Очищаем начало строки от знаков
    clean_text = lower_text.lstrip(".,!?¡¿- ")
    
    for trigger in triggers:
        # Проверяем, начинается ли текст с триггера
        if clean_text.startswith(trigger):
            
            # Находим, где кончается триггер
            start_index = clean_text.find(trigger) + len(trigger)
            # Отрезаем триггер, получаем "остаток" (например: " une recette de boeuf")
            remaining = clean_text[start_index:].strip()
            
            # --- ЧИСТКА "МУСОРНЫХ" СЛОВ ---
            # Удаляем артикли и предлоги в начале блюда, чтобы не искать рецепт "a pizza" или "une pizza"
            # EN: a, an, the, for, of
            # FR: un, une, le, la, les, du, de, des, pour
            # DE: ein, eine, der, die, das, für, von
            # ES: un, una, el, la, los, las, para, de
            # IT: un, una, il, la, lo, per, di
            
            junk_pattern = r'^(a|an|the|for|of|about|' \
                           r'un|une|le|la|les|l\'|du|de|des|pour|' \
                           r'ein|eine|einen|der|die|das|für|von|' \
                           r'el|los|las|para|' \
                           r'il|lo|per|di)\s+'
            
            # Чистим (флаг IGNORECASE уже учтен, т.к. работаем с lower_text)
            dish_name = re.sub(junk_pattern, '', remaining)
            
            # Также удаляем слово "recette"/"recipe" повторно, если фраза была "Donne moi une recette de..."
            # Триггер "donne-moi" съел первую часть, осталось "une recette de..."
            if dish_name.startswith("recipe ") or dish_name.startswith("recette ") or \
               dish_name.startswith("rezept ") or dish_name.startswith("ricetta ") or dish_name.startswith("receta "):
                   dish_name = dish_name.split(' ', 1)[1] # Отрезаем первое слово
                   # И снова чистим предлоги (of, de, ...)
                   dish_name = re.sub(junk_pattern, '', dish_name.strip())

            # Если после всех чисток что-то осталось — это и есть блюдо!
            if dish_name and len(dish_name) > 1:
                return dish_name.rstrip('.?!')

    return None

# --- ГЕНЕРАЦИЯ И ОТПРАВКА ---
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

        await track_safely(user_id, "recipe_generated", {
            "dish_name": dish_name, 
            "language": lang, 
            "type": "direct" if is_direct else "selection"
        })
        
        # ХАК ДЛЯ ПРЯМЫХ ЗАПРОСОВ (Чтобы кнопки работали с индексом 0)
        if is_direct:
            fake_dishes = [{"name": dish_name, "category": "direct"}]
            state_manager.set_generated_dishes(user_id, fake_dishes)
            state_manager.set_current_dish(user_id, fake_dishes[0])
            dish_index = 0
        else:
             dishes = state_manager.get_generated_dishes(user_id) or []
             dish_index = next((i for i, d in enumerate(dishes) if d['name'] == dish_name), 0)
             if dishes and dish_index < len(dishes):
                  state_manager.set_current_dish(user_id, dishes[dish_index])
        
        # Кнопки
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
            builder.row(
                InlineKeyboardButton(text=get_text(lang, "btn_another"), callback_data=another_cb),
                InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="back_to_categories")
            )
        
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