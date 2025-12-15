import logging
from aiogram import Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
from config import FAVORITES_PER_PAGE

logger = logging.getLogger(__name__)

async def handle_favorite_pagination(callback: CallbackQuery):
    """Ž¡à ¡ âë¢ ¥â ¯ £¨­ æ¨î ¢ ¨§¡à ­­®¬"""
    user_id = callback.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ˆ§¢«¥ª ¥¬ ­®¬¥à áâà ­¨æë ¨§ callback_data (fav_page_1 -> 1)
    try:
        page = int(callback.data.split('_')[2])
    except (IndexError, ValueError):
        page = 1
    
    # ®«ãç ¥¬ ¨§¡à ­­ë¥ à¥æ¥¯âë ¤«ï áâà ­¨æë
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page)
    
    if not favorites:
        await callback.message.edit_text(get_text(lang, "favorites_empty"))
        await callback.answer()
        return
    
    # ”®à¬ â¨àã¥¬ á¯¨á®ª à¥æ¥¯â®¢
    recipes_text = ""
    for i, fav in enumerate(favorites, 1):
        # ‚ëç¨á«ï¥¬ ­®¬¥à ­  áâà ­¨æ¥
        item_num = (page - 1) * FAVORITES_PER_PAGE + i
        date_str = fav['created_at'].strftime("%d.%m.%Y")
        recipes_text += get_text(lang, "favorites_recipe_item", 
                               num=item_num, dish=fav['dish_name'], date=date_str)
    
    # ‘®§¤ ñ¬ ª« ¢¨ âãàã á ¯ £¨­ æ¨¥©
    builder = InlineKeyboardBuilder()
    
    # Š­®¯ª¨ ¯ £¨­ æ¨¨ (â®«ìª® ¥á«¨ ¡®«ìè¥ ®¤­®© áâà ­¨æë)
    if total_pages > 1:
        buttons = []
        
        # Š­®¯ª  "­ § ¤"
        if page > 1:
            buttons.append(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_prev"),
                    callback_data=f"fav_page_{page - 1}"
                )
            )
        
        # ®¬¥à áâà ­¨æë
        buttons.append(
            InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data="noop"
            )
        )
        
        # Š­®¯ª  "¢¯¥àñ¤"
        if page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_next"),
                    callback_data=f"fav_page_{page + 1}"
                )
            )
        
        builder.row(*buttons)
    
    # Š­®¯ª  ã¤ «¥­¨ï à¥æ¥¯â  ¨ ¢®§¢à â 
    if favorites:
        first_fav = favorites[0]
        builder.row(
            InlineKeyboardButton(
                text="??? “¤ «¨âì íâ®â à¥æ¥¯â",
                callback_data=f"delete_fav_{first_fav['dish_name']}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    # Žâ¯à ¢«ï¥¬ ®¡­®¢«ñ­­®¥ á®®¡é¥­¨¥
    text = get_text(lang, "favorites_list", page=page, total_pages=total_pages, recipes=recipes_text)
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()
    
    # ‹®£¨àã¥¬ ¯à®á¬®âà áâà ­¨æë
    await metrics.track_event(user_id, "favorites_page_viewed", {"page": page, "total_pages": total_pages})

async def handle_add_to_favorites(callback: CallbackQuery):
    """„®¡ ¢«ï¥â à¥æ¥¯â ¢ ¨§¡à ­­®¥"""
    user_id = callback.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ˆ§¢«¥ª ¥¬ ¤ ­­ë¥ ¨§ callback_data (add_fav_1 -> ¨­¤¥ªá 1)
    try:
        dish_index = int(callback.data.split('_')[2])
        
        # ®«ãç ¥¬ â¥ªãé¥¥ ¡«î¤® ¨§ state_manager
        from state_manager import state_manager
        dish_name = state_manager.get_generated_dish(user_id, dish_index)
        
        if not dish_name:
            await callback.answer("Žè¨¡ª : ¡«î¤® ­¥ ­ ©¤¥­®")
            return
        
        # ®«ãç ¥¬ à¥æ¥¯â (­ã¦­® á®åà ­¨âì ¥£® â¥ªáâ)
        # ‚ à¥ «ì­®© à¥ «¨§ æ¨¨ §¤¥áì ­ã¦­® ¯®«ãç¨âì â¥ªáâ à¥æ¥¯â 
        # „«ï ¯à¨¬¥à  á®§¤ ñ¬ ä¨ªâ¨¢­ë© à¥æ¥¯â
        recipe_text = f"¥æ¥¯â ¤«ï {dish_name}\n\nâ®â à¥æ¥¯â ¡ë« á®åà ­ñ­ ¢ ¨§¡à ­­®¥."
        
        # ®«ãç ¥¬ â¥ªãé¨¥ ¯à®¤ãªâë
        products = state_manager.get_products(user_id) or ""
        
        # ‘®§¤ ñ¬ § ¯¨áì ¢ ¨§¡à ­­®¬
        from database.models import FavoriteRecipe, Category
        favorite = FavoriteRecipe(
            user_id=user_id,
            dish_name=dish_name,
            recipe_text=recipe_text,
            ingredients=products,
            language=lang
        )
        
        # ‘®åà ­ï¥¬ ¢ ¡ §ã
        success = await favorites_repo.add_favorite(favorite)
        
        if success:
            await callback.answer(get_text(lang, "recipe_added_to_fav"))
            
            # ‹®£¨àã¥¬ ¤®¡ ¢«¥­¨¥ ¢ ¨§¡à ­­®¥
            await metrics.track_favorite_added(user_id, dish_name, lang)
            
            # Ž¡­®¢«ï¥¬ ª­®¯ªã (¬¥­ï¥¬ ­  "¢ ¨§¡à ­­®¬")
            await update_favorite_button(callback, dish_index, True, lang)
        else:
            await callback.answer("? Žè¨¡ª  ¯à¨ á®åà ­¥­¨¨")
            
    except (IndexError, ValueError) as e:
        logger.error(f"Žè¨¡ª  ®¡à ¡®âª¨ ¤®¡ ¢«¥­¨ï ¢ ¨§¡à ­­®¥: {e}")
        await callback.answer("? Žè¨¡ª ")

async def handle_remove_from_favorites(callback: CallbackQuery):
    """“¤ «ï¥â à¥æ¥¯â ¨§ ¨§¡à ­­®£®"""
    user_id = callback.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ˆ§¢«¥ª ¥¬ ­ §¢ ­¨¥ ¡«î¤  ¨§ callback_data (remove_fav_pizza_margherita)
    try:
        # callback_data: remove_fav_dishname (dishname ¬®¦¥â á®¤¥à¦ âì ¯®¤çñàª¨¢ ­¨ï)
        parts = callback.data.split('_')[2:]  # à®¯ãáª ¥¬ remove_fav
        dish_name = '_'.join(parts)
        
        if not dish_name:
            await callback.answer("Žè¨¡ª : ­ §¢ ­¨¥ ¡«î¤  ­¥ ãª § ­®")
            return
        
        # “¤ «ï¥¬ ¨§ ¨§¡à ­­®£®
        success = await favorites_repo.remove_favorite(user_id, dish_name)
        
        if success:
            await callback.answer(get_text(lang, "recipe_removed_from_fav"))
            
            # ‹®£¨àã¥¬ ã¤ «¥­¨¥ ¨§ ¨§¡à ­­®£®
            await metrics.track_event(user_id, "favorite_removed", {"dish_name": dish_name})
            
            # Ž¡­®¢«ï¥¬ ª­®¯ªã (¬¥­ï¥¬ ­  "¤®¡ ¢¨âì ¢ ¨§¡à ­­®¥")
            # ã¦­® ­ ©â¨ ¨­¤¥ªá ¡«î¤ 
            from state_manager import state_manager
            dishes = state_manager.get_generated_dishes(user_id)
            for i, dish in enumerate(dishes):
                if dish.get('name') == dish_name:
                    await update_favorite_button(callback, i, False, lang)
                    break
        else:
            await callback.answer("? Žè¨¡ª  ¯à¨ ã¤ «¥­¨¨")
            
    except Exception as e:
        logger.error(f"Žè¨¡ª  ®¡à ¡®âª¨ ã¤ «¥­¨ï ¨§ ¨§¡à ­­®£®: {e}")
        await callback.answer("? Žè¨¡ª ")

async def handle_delete_favorite(callback: CallbackQuery):
    """“¤ «ï¥â à¥æ¥¯â ¨§ ¨§¡à ­­®£® (¨§ á¯¨áª  ¨§¡à ­­®£®)"""
    user_id = callback.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ˆ§¢«¥ª ¥¬ ­ §¢ ­¨¥ ¡«î¤  ¨§ callback_data (delete_fav_pizza_margherita)
    try:
        parts = callback.data.split('_')[2:]  # à®¯ãáª ¥¬ delete_fav
        dish_name = '_'.join(parts)
        
        if not dish_name:
            await callback.answer("Žè¨¡ª : ­ §¢ ­¨¥ ¡«î¤  ­¥ ãª § ­®")
            return
        
        # “¤ «ï¥¬ ¨§ ¨§¡à ­­®£®
        success = await favorites_repo.remove_favorite(user_id, dish_name)
        
        if success:
            await callback.answer(get_text(lang, "recipe_removed_from_fav"))
            
            # Ž¡­®¢«ï¥¬ á¯¨á®ª ¨§¡à ­­®£®
            # à®áâ® ã¤ «ï¥¬ á®®¡é¥­¨¥ ¨ ¯®ª §ë¢ ¥¬ ®¡­®¢«ñ­­ë© á¯¨á®ª
            await callback.message.delete()
            
            # ®ª §ë¢ ¥¬ ¯¥à¢ãî áâà ­¨æã ¨§¡à ­­®£®
            favorites, total_pages = await favorites_repo.get_favorites_page(user_id, 1)
            
            if not favorites:
                await callback.message.answer(get_text(lang, "favorites_empty"))
                return
            
            # ”®à¬ â¨àã¥¬ á¯¨á®ª
            recipes_text = ""
            for i, fav in enumerate(favorites, 1):
                date_str = fav['created_at'].strftime("%d.%m.%Y")
                recipes_text += get_text(lang, "favorites_recipe_item", 
                                       num=i, dish=fav['dish_name'], date=date_str)
            
            # ‘®§¤ ñ¬ ª« ¢¨ âãàã
            builder = InlineKeyboardBuilder()
            
            if total_pages > 1:
                builder.row(
                    InlineKeyboardButton(
                        text=get_text(lang, "btn_prev"),
                        callback_data="fav_page_1"
                    ),
                    InlineKeyboardButton(
                        text=f"1/{total_pages}",
                        callback_data="noop"
                    ),
                    InlineKeyboardButton(
                        text=get_text(lang, "btn_next"),
                        callback_data="fav_page_2"
                    )
                )
            
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_back"),
                    callback_data="main_menu"
                )
            )
            
            text = get_text(lang, "favorites_list", page=1, total_pages=total_pages, recipes=recipes_text)
            await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
            
            # ‹®£¨àã¥¬ ã¤ «¥­¨¥
            await metrics.track_event(user_id, "favorite_deleted_from_list", {"dish_name": dish_name})
            
        else:
            await callback.answer("? Žè¨¡ª  ¯à¨ ã¤ «¥­¨¨")
            
    except Exception as e:
        logger.error(f"Žè¨¡ª  ã¤ «¥­¨ï ¨§ ¨§¡à ­­®£®: {e}")
        await callback.answer("? Žè¨¡ª ")

async def update_favorite_button(callback: CallbackQuery, dish_index: int, is_favorite: bool, lang: str):
    """Ž¡­®¢«ï¥â ª­®¯ªã ¨§¡à ­­®£® ¢ á®®¡é¥­¨¨ á à¥æ¥¯â®¬"""
    try:
        # ®«ãç ¥¬ â¥ªãéãî ª« ¢¨ âãàã
        keyboard = callback.message.reply_markup
        
        if not keyboard:
            return
        
        # ‘®§¤ ñ¬ ­®¢ãî ª« ¢¨ âãàã
        builder = InlineKeyboardBuilder()
        
        # Š®¯¨àã¥¬ ¢á¥ áâà®ª¨ ª­®¯®ª, ¨§¬¥­ïï ­ã¦­ãî ª­®¯ªã
        for row in keyboard.inline_keyboard:
            new_row = []
            for button in row:
                if button.callback_data and f"dish_{dish_index}" in button.callback_data:
                    # â® ª­®¯ª  ¡«î¤ , ®áâ ¢«ï¥¬ ª ª ¥áâì
                    new_row.append(button)
                elif button.callback_data and ("add_fav" in button.callback_data or "remove_fav" in button.callback_data):
                    # â® ª­®¯ª  ¨§¡à ­­®£®, ®¡­®¢«ï¥¬ ¥ñ
                    if is_favorite:
                        new_button = InlineKeyboardButton(
                            text=get_text(lang, "btn_remove_from_fav"),
                            callback_data=f"remove_fav_{dish_index}"
                        )
                    else:
                        new_button = InlineKeyboardButton(
                            text=get_text(lang, "btn_add_to_fav"),
                            callback_data=f"add_fav_{dish_index}"
                        )
                    new_row.append(new_button)
                else:
                    # „àã£¨¥ ª­®¯ª¨ ®áâ ¢«ï¥¬ ª ª ¥áâì
                    new_row.append(button)
            
            if new_row:
                builder.row(*new_row)
        
        # Ž¡­®¢«ï¥¬ á®®¡é¥­¨¥
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Žè¨¡ª  ®¡­®¢«¥­¨ï ª­®¯ª¨ ¨§¡à ­­®£®: {e}")

def register_favorites_handlers(dp: Dispatcher):
    """¥£¨áâà¨àã¥â ®¡à ¡®âç¨ª¨ ¤«ï ¨§¡à ­­®£®"""
    dp.callback_query.register(handle_favorite_pagination, F.data.startswith("fav_page_"))
    dp.callback_query.register(handle_add_to_favorites, F.data.startswith("add_fav_"))
    dp.callback_query.register(handle_remove_from_favorites, F.data.startswith("remove_fav_"))
    dp.callback_query.register(handle_delete_favorite, F.data.startswith("delete_fav_"))
