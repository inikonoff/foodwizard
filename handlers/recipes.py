import logging
from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from services.groq_service import groq_service
from locales.texts import get_text
from state_manager import state_manager

logger = logging.getLogger(__name__)

async def handle_text_message(message: Message):
    """Ž¡à ¡ âë¢ ¥â â¥ªáâ®¢ë¥ á®®¡é¥­¨ï á ¯à®¤ãªâ ¬¨"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # à®¢¥àï¥¬ «¨¬¨âë
    allowed, used, limit = await users_repo.check_and_increment_request(user_id, "text")
    
    if not allowed:
        # ®«ãç ¥¬ ï§ëª ¤«ï á®®¡é¥­¨ï ®¡ ®è¨¡ª¥
        user_data = await users_repo.get_user(user_id)
        lang = user_data.get('language_code', 'ru') if user_data else 'ru'
        
        await message.answer(
            f"? <b>‹¨¬¨â ¨áç¥à¯ ­!</b>\n\n"
            f"‚ë ¨á¯®«ì§®¢ «¨ {used} ¨§ {limit} â¥ªáâ®¢ëå § ¯à®á®¢ á¥£®¤­ï.\n"
            f"‹¨¬¨âë ®¡­®¢«ïîâáï ª ¦¤ë© ¤¥­ì ¢ 00:00.\n\n"
            f"?? <b>•®â¨â¥ ¡®«ìè¥?</b> ˆá¯®«ì§ã©â¥ ª®¬ ­¤ã /stats",
            parse_mode="HTML"
        )
        return
    
    # ®«ãç ¥¬ ï§ëª ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # à®¢¥àï¥¬, ï¢«ï¥âáï «¨ íâ® ¯àï¬ë¬ § ¯à®á®¬ à¥æ¥¯â 
    direct_keywords = ["à¥æ¥¯â ", "recipe ", "à¥æ¥¯â ¤«ï ", "recipe for ", "¤ © à¥æ¥¯â "]
    if any(text.lower().startswith(keyword) for keyword in direct_keywords):
        await handle_direct_recipe_request(message, text, lang)
        return
    
    # à®¢¥àï¥¬ ¯ áå «ª¨
    if text.lower() in ["á¯ á¨¡®", "thanks", "danke", "merci", "grazie", "gracias"]:
        await message.answer(get_text(lang, "thanks"))
        return
    
    # à®¢¥àï¥¬ ¤«¨­ã á®®¡é¥­¨ï
    if len(text) > 1000:
        await message.answer(get_text(lang, "error_too_long"))
        return
    
    # ®«ãç ¥¬ â¥ªãé¨¥ ¯à®¤ãªâë
    current_products = state_manager.get_products(user_id)
    
    # …á«¨ ¯à®¤ãªâ®¢ ¥éñ ­¥â, ¯à®¢¥àï¥¬ ¢ «¨¤­®áâì
    if not current_products:
        is_valid = await groq_service.validate_ingredients(text, lang)
        if not is_valid:
            await message.answer(get_text(lang, "error_no_products"))
            return
        
        # ‘®åà ­ï¥¬ ¯à®¤ãªâë
        state_manager.set_products(user_id, text)
        await message.answer(get_text(lang, "products_accepted", products=text))
        
        # €­ «¨§¨àã¥¬ ª â¥£®à¨¨
        await analyze_and_show_categories(message, user_id, text, lang)
    else:
        # „®¡ ¢«ï¥¬ ª áãé¥áâ¢ãîé¨¬ ¯à®¤ãªâ ¬
        state_manager.append_products(user_id, text)
        all_products = state_manager.get_products(user_id)
        await message.answer(get_text(lang, "products_added", products=text))
        
        # ®ª §ë¢ ¥¬ ª â¥£®à¨¨ á ãçñâ®¬ ­®¢ëå ¯à®¤ãªâ®¢
        await analyze_and_show_categories(message, user_id, all_products, lang)
    
    # Ž¡­®¢«ï¥¬  ªâ¨¢­®áâì ¯®«ì§®¢ â¥«ï
    await users_repo.update_activity(user_id)

async def handle_direct_recipe_request(message: Message, text: str, lang: str):
    """Ž¡à ¡ âë¢ ¥â ¯àï¬®© § ¯à®á à¥æ¥¯â  (­ ¯à¨¬¥à, "à¥æ¥¯â ¯¨ææë")"""
    user_id = message.from_user.id
    
    # ˆ§¢«¥ª ¥¬ ­ §¢ ­¨¥ ¡«î¤ 
    # “¤ «ï¥¬ ª«îç¥¢ë¥ á«®¢  ¨ «¨è­¨¥ ¯à®¡¥«ë
    keywords = ["à¥æ¥¯â", "recipe", "à¥æ¥¯â ¤«ï", "recipe for", "¤ © à¥æ¥¯â"]
    dish_name = text.lower()
    for keyword in keywords:
        dish_name = dish_name.replace(keyword, "").strip()
    
    if not dish_name or len(dish_name) < 2:
        await message.answer(get_text(lang, "error_no_products"))
        return
    
    # ®ª §ë¢ ¥¬ á®®¡é¥­¨¥ ® ®¡à ¡®âª¥
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    try:
        # ƒ¥­¥à¨àã¥¬ à¥æ¥¯â
        recipe = await groq_service.generate_freestyle_recipe(dish_name, lang)
        
        await wait_msg.delete()
        
        if not recipe or "?" in recipe:
            await message.answer(get_text(lang, "error_generation"))
            return
        
        # à®¢¥àï¥¬, ¥áâì «¨ ã¦¥ ¢ ¨§¡à ­­®¬
        is_favorite = await favorites_repo.is_favorite(user_id, dish_name)
        
        # ‘®§¤ ñ¬ ª« ¢¨ âãàã á ª­®¯ª ¬¨
        builder = InlineKeyboardBuilder()
        
        # Š­®¯ª  ¨§¡à ­­®£®
        if is_favorite:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_remove_from_fav"),
                    callback_data=f"remove_fav_direct_{dish_name.replace(' ', '_')}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_add_to_fav"),
                    callback_data=f"add_fav_direct_{dish_name.replace(' ', '_')}"
                )
            )
        
        # Š­®¯ª  ¤àã£®£® ¢ à¨ ­â 
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_another"),
                callback_data=f"repeat_recipe_{dish_name.replace(' ', '_')}"
            )
        )
        
        # Žâ¯à ¢«ï¥¬ à¥æ¥¯â
        await message.answer(recipe, reply_markup=builder.as_markup(), parse_mode="Markdown")
        
        # ‹®£¨àã¥¬ £¥­¥à æ¨î à¥æ¥¯â 
        await metrics.track_recipe_generated(
            user_id=user_id,
            dish_name=dish_name,
            lang=lang,
            category="direct",
            ingredients_count=0,
            cache_hit=False
        )
        
    except Exception as e:
        logger.error(f"Žè¨¡ª  £¥­¥à æ¨¨ à¥æ¥¯â : {e}")
        await wait_msg.delete()
        await message.answer(get_text(lang, "error_generation"))

async def analyze_and_show_categories(message: Message, user_id: int, products: str, lang: str):
    """€­ «¨§¨àã¥â ¯à®¤ãªâë ¨ ¯®ª §ë¢ ¥â ª â¥£®à¨¨"""
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    try:
        # €­ «¨§¨àã¥¬ ª â¥£®à¨¨
        categories = await groq_service.analyze_products(products, lang)
        
        await wait_msg.delete()
        
        if not categories:
            await message.answer(get_text(lang, "error_generation"))
            return
        
        # ‘®åà ­ï¥¬ ª â¥£®à¨¨ ¢ á®áâ®ï­¨¨
        state_manager.set_categories(user_id, categories)
        
        # ‘®§¤ ñ¬ ª« ¢¨ âãàã á ª â¥£®à¨ï¬¨
        builder = InlineKeyboardBuilder()
        
        for category in categories:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, category),
                    callback_data=f"cat_{category}"
                )
            )
        
        # Š­®¯ª  á¡à®á 
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_restart"),
                callback_data="restart"
            )
        )
        
        await message.answer(
            get_text(lang, "choose_category"),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Žè¨¡ª   ­ «¨§  ª â¥£®à¨©: {e}")
        await wait_msg.delete()
        await message.answer(get_text(lang, "error_generation"))

async def handle_category_selection(callback: CallbackQuery):
    """Ž¡à ¡ âë¢ ¥â ¢ë¡®à ª â¥£®à¨¨"""
    user_id = callback.from_user.id
    category = callback.data.split('_')[1]  # cat_soup -> soup
    
    # ®«ãç ¥¬ ï§ëª ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ®«ãç ¥¬ ¯à®¤ãªâë
    products = state_manager.get_products(user_id)
    
    if not products:
        await callback.answer("‘­ ç «  ®â¯à ¢ìâ¥ ¯à®¤ãªâë")
        return
    
    wait_msg = await callback.message.answer(get_text(lang, "processing"))
    
    try:
        # ƒ¥­¥à¨àã¥¬ á¯¨á®ª ¡«î¤
        dishes = await groq_service.generate_dish_list(products, category, lang)
        
        await wait_msg.delete()
        
        if not dishes:
            await callback.message.answer(get_text(lang, "error_generation"))
            await callback.answer()
            return
        
        # ‘®åà ­ï¥¬ ¡«î¤  ¢ á®áâ®ï­¨¨
        state_manager.set_generated_dishes(user_id, dishes)
        
        # ‘®§¤ ñ¬ ª« ¢¨ âãàã á ¡«î¤ ¬¨
        builder = InlineKeyboardBuilder()
        
        for i, dish in enumerate(dishes):
            dish_name = dish.get('name', f'«î¤® {i+1}')
            # Ž¡à¥§ ¥¬ ¤«¨­­ë¥ ­ §¢ ­¨ï
            if len(dish_name) > 35:
                dish_name = dish_name[:32] + "..."
            
            builder.row(
                InlineKeyboardButton(
                    text=dish_name,
                    callback_data=f"dish_{i}"
                )
            )
        
        # Š­®¯ª¨ ­ ¢¨£ æ¨¨
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_back"),
                callback_data="back_to_categories"
            ),
            InlineKeyboardButton(
                text=get_text(lang, "btn_restart"),
                callback_data="restart"
            )
        )
        
        await callback.message.edit_text(
            get_text(lang, "choose_dish"),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Žè¨¡ª  £¥­¥à æ¨¨ á¯¨áª  ¡«î¤: {e}")
        await wait_msg.delete()
        await callback.answer("? Žè¨¡ª  £¥­¥à æ¨¨")

async def handle_dish_selection(callback: CallbackQuery):
    """Ž¡à ¡ âë¢ ¥â ¢ë¡®à ¡«î¤ """
    user_id = callback.from_user.id
    dish_index = int(callback.data.split('_')[1])  # dish_0 -> 0
    
    # ®«ãç ¥¬ ï§ëª ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ®«ãç ¥¬ ¡«î¤®
    dishes = state_manager.get_generated_dishes(user_id)
    if not dishes or dish_index >= len(dishes):
        await callback.answer("«î¤® ­¥ ­ ©¤¥­®")
        return
    
    dish = dishes[dish_index]
    dish_name = dish.get('name')
    
    # ®«ãç ¥¬ ¯à®¤ãªâë
    products = state_manager.get_products(user_id) or ""
    
    wait_msg = await callback.message.answer(get_text(lang, "processing"))
    
    try:
        # ƒ¥­¥à¨àã¥¬ à¥æ¥¯â
        recipe = await groq_service.generate_recipe(dish_name, products, lang)
        
        await wait_msg.delete()
        
        if not recipe or "?" in recipe:
            await callback.message.answer(get_text(lang, "error_generation"))
            await callback.answer()
            return
        
        # ‘®åà ­ï¥¬ â¥ªãé¥¥ ¡«î¤®
        state_manager.set_current_dish(user_id, dish_name)
        
        # à®¢¥àï¥¬, ¥áâì «¨ ã¦¥ ¢ ¨§¡à ­­®¬
        is_favorite = await favorites_repo.is_favorite(user_id, dish_name)
        
        # ‘®§¤ ñ¬ ª« ¢¨ âãàã
        builder = InlineKeyboardBuilder()
        
        # Š­®¯ª  ¨§¡à ­­®£®
        if is_favorite:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_remove_from_fav"),
                    callback_data=f"remove_fav_{dish_index}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_add_to_fav"),
                    callback_data=f"add_fav_{dish_index}"
                )
            )
        
        # Š­®¯ª¨ ­ ¢¨£ æ¨¨
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_another"),
                callback_data=f"repeat_dish_{dish_index}"
            ),
            InlineKeyboardButton(
                text=get_text(lang, "btn_to_categories"),
                callback_data="back_to_categories"
            )
        )
        
        await callback.message.answer(recipe, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await callback.answer()
        
        # ‹®£¨àã¥¬ £¥­¥à æ¨î à¥æ¥¯â 
        await metrics.track_recipe_generated(
            user_id=user_id,
            dish_name=dish_name,
            lang=lang,
            category=state_manager.get_categories(user_id)[0] if state_manager.get_categories(user_id) else "unknown",
            ingredients_count=len(products.split(',')),
            cache_hit=False
        )
        
    except Exception as e:
        logger.error(f"Žè¨¡ª  £¥­¥à æ¨¨ à¥æ¥¯â : {e}")
        await wait_msg.delete()
        await callback.answer("? Žè¨¡ª ")

async def handle_back_to_categories(callback: CallbackQuery):
    """‚®§¢à é ¥â ª ¢ë¡®àã ª â¥£®à¨©"""
    user_id = callback.from_user.id
    
    # ®«ãç ¥¬ ï§ëª ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ®«ãç ¥¬ ª â¥£®à¨¨
    categories = state_manager.get_categories(user_id)
    
    if not categories:
        await callback.answer("¥â á®åà ­ñ­­ëå ª â¥£®à¨©")
        return
    
    # ‘®§¤ ñ¬ ª« ¢¨ âãàã á ª â¥£®à¨ï¬¨
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, category),
                callback_data=f"cat_{category}"
            )
        )
    
    # Š­®¯ª  á¡à®á 
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_restart"),
            callback_data="restart"
        )
    )
    
    await callback.message.edit_text(
        get_text(lang, "choose_category"),
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

async def handle_restart(callback: CallbackQuery):
    """‘¡à áë¢ ¥â á¥áá¨î"""
    user_id = callback.from_user.id
    
    # ®«ãç ¥¬ ï§ëª ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Žç¨é ¥¬ á¥áá¨î
    state_manager.clear_session(user_id)
    
    await callback.message.edit_text(
        get_text(lang, "start_manual"),
        parse_mode="Markdown"
    )
    await callback.answer()

async def handle_repeat_recipe(callback: CallbackQuery):
    """ƒ¥­¥à¨àã¥â ¤àã£®© ¢ à¨ ­â à¥æ¥¯â """
    user_id = callback.from_user.id
    
    # à®¢¥àï¥¬ «¨¬¨âë
    allowed, used, limit = await users_repo.check_and_increment_request(user_id, "text")
    
    if not allowed:
        # ®«ãç ¥¬ ï§ëª ¤«ï á®®¡é¥­¨ï ®¡ ®è¨¡ª¥
        user_data = await users_repo.get_user(user_id)
        lang = user_data.get('language_code', 'ru') if user_data else 'ru'
        
        await callback.answer(
            f"? ‹¨¬¨â ¨áç¥à¯ ­! {used}/{limit}",
            show_alert=True
        )
        return
    
    # ®«ãç ¥¬ ï§ëª ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ˆ§¢«¥ª ¥¬ ­ §¢ ­¨¥ ¡«î¤  ¨«¨ ¨­¤¥ªá
    data_parts = callback.data.split('_')
    
    if len(data_parts) >= 3 and data_parts[1] == "recipe":
        # àï¬®© à¥æ¥¯â (repeat_recipe_pizza)
        dish_name = '_'.join(data_parts[2:])
        products = ""
    elif len(data_parts) >= 3 and data_parts[1] == "dish":
        # ¥æ¥¯â ¨§ á¯¨áª  (repeat_dish_0)
        dish_index = int(data_parts[2])
        dishes = state_manager.get_generated_dishes(user_id)
        if not dishes or dish_index >= len(dishes):
            await callback.answer("«î¤® ­¥ ­ ©¤¥­®")
            return
        dish_name = dishes[dish_index].get('name')
        products = state_manager.get_products(user_id) or ""
    else:
        # ’¥ªãé¥¥ ¡«î¤®
        dish_name = state_manager.get_current_dish(user_id)
        products = state_manager.get_products(user_id) or ""
    
    if not dish_name:
        await callback.answer("«î¤® ­¥ ¢ë¡à ­®")
        return
    
    wait_msg = await callback.message.answer(get_text(lang, "processing"))
    
    try:
        if products:
            recipe = await groq_service.generate_recipe(dish_name, products, lang)
        else:
            recipe = await groq_service.generate_freestyle_recipe(dish_name, lang)
        
        await wait_msg.delete()
        
        if not recipe or "?" in recipe:
            await callback.message.answer(get_text(lang, "error_generation"))
            await callback.answer()
            return
        
        # à®¢¥àï¥¬, ¥áâì «¨ ã¦¥ ¢ ¨§¡à ­­®¬
        is_favorite = await favorites_repo.is_favorite(user_id, dish_name)
        
        # ‘®§¤ ñ¬ ª« ¢¨ âãàã
        builder = InlineKeyboardBuilder()
        
        # Š­®¯ª  ¨§¡à ­­®£®
        if is_favorite:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_remove_from_fav"),
                    callback_data=f"remove_fav_{dish_name.replace(' ', '_')}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_add_to_fav"),
                    callback_data=f"add_fav_{dish_name.replace(' ', '_')}"
                )
            )
        
        # Š­®¯ª¨ ­ ¢¨£ æ¨¨
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_another"),
                callback_data=callback.data  # ®¢â®à¨âì â®â ¦¥ § ¯à®á
            ),
            InlineKeyboardButton(
                text=get_text(lang, "btn_back"),
                callback_data="back_to_categories"
            )
        )
        
        # Žâ¯à ¢«ï¥¬ ­®¢ë© à¥æ¥¯â
        await callback.message.answer(recipe, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Žè¨¡ª  ¯®¢â®à­®© £¥­¥à æ¨¨ à¥æ¥¯â : {e}")
        await wait_msg.delete()
        await callback.answer("? Žè¨¡ª ")

def register_recipe_handlers(dp: Dispatcher):
    """¥£¨áâà¨àã¥â ®¡à ¡®âç¨ª¨ à¥æ¥¯â®¢"""
    # ’¥ªáâ®¢ë¥ á®®¡é¥­¨ï
    dp.message.register(handle_text_message, F.text)
    
    # Š®««¡íª¨
    dp.callback_query.register(handle_category_selection, F.data.startswith("cat_"))
    dp.callback_query.register(handle_dish_selection, F.data.startswith("dish_"))
    dp.callback_query.register(handle_back_to_categories, F.data == "back_to_categories")
    dp.callback_query.register(handle_restart, F.data == "restart")
    dp.callback_query.register(handle_repeat_recipe, F.data.startswith(("repeat_recipe_", "repeat_dish_")))
