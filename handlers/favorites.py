import logging
from aiogram import Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from state_manager import state_manager
from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
from config import FAVORITES_PER_PAGE, FREE_USER_LIMITS
from database.models import FavoriteRecipe, Category

logger = logging.getLogger(__name__)

async def track_safely(user_id: int, event_name: str, data: dict = None):
    try: await metrics.track_event(user_id, event_name, data)
    except: pass

async def handle_favorite_pagination(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    
    try:
        # Пробуем достать номер страницы из "fav_page_X"
        page_str = callback.data.split('_')[2]
        page = int(page_str)
    except (IndexError, ValueError):
        # Если data = "show_favorites" (кнопка меню)
        page = 1
    
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page)
    
    if not favorites:
        # Используем try-except, чтобы отправить новое сообщение, если старое нельзя отредактировать (например, из-за картинки)
        try: await callback.message.edit_text(get_text(lang, "favorites_empty"))
        except: await callback.message.answer(get_text(lang, "favorites_empty"))
        return 
    
    # Форматируем заголовок без звездочек
    header = get_text(lang, "favorites_title").replace("**", "") + f" ({page}/{total_pages})"
    
    builder = InlineKeyboardBuilder()
    for fav in favorites:
        btn_text = f"{fav['dish_name']} ({fav['created_at'].strftime('%d.%m')})"
        builder.row(InlineKeyboardButton(text=btn_text, callback_data=f"view_fav_{fav['id']}"))
    
    if total_pages > 1:
        row = []
        if page > 1: row.append(InlineKeyboardButton(text="⬅️", callback_data=f"fav_page_{page - 1}"))
        row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages: row.append(InlineKeyboardButton(text="➡️", callback_data=f"fav_page_{page + 1}"))
        builder.row(*row)
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    # Используем HTML для форматирования заголовка
    await callback.message.edit_text(f"<b>{header}</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await track_safely(user_id, "favorites_page_viewed", {"page": page})


async def handle_view_favorite(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        fav_id = int(callback.data.split('_')[2])
        recipe = await favorites_repo.get_favorite_by_id(fav_id)
        
        if not recipe:
            await callback.answer("Not found")
            return
            
        full_text = f"🍳 <b>{recipe['dish_name']}</b>\n\n{recipe['recipe_text']}\n\n🛒 <i>{recipe.get('ingredients', '')}</i>"
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_fav_id_{fav_id}"))
        builder.row(InlineKeyboardButton(text="🔙 List", callback_data="fav_page_1"))
        
        await callback.message.edit_text(full_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await callback.answer()
    except Exception as e:
        logger.error(f"View Error: {e}")
        await callback.answer("Error")


async def handle_delete_favorite_by_id(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        fav_id = int(callback.data.split('_')[3])
        fav = await favorites_repo.get_favorite_by_id(fav_id)
        if not fav:
            await callback.answer("Already deleted")
            # Возвращаемся на первую страницу
            callback.data = "fav_page_1"
            await handle_favorite_pagination(callback)
            return

        success = await favorites_repo.remove_favorite(user_id, fav['dish_name'])
        if success:
            await callback.answer("🗑 Deleted")
            callback.data = "fav_page_1" 
            await handle_favorite_pagination(callback)
        else:
            await callback.answer("Delete Error")
            
    except Exception as e:
        logger.error(f"Del Error: {e}")
        await callback.answer("Error")

# --- ДОБАВЛЕНИЕ С МЯГКИМ ЛИМИТОМ ---
async def handle_add_to_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    is_premium = user_data.get('is_premium', False)

    try:
        # 1. ПРОВЕРКА ЛИМИТА
        if not is_premium:
            current_count = await favorites_repo.count_favorites(user_id)
            if current_count >= FREE_USER_LIMITS["max_favorites"]: # 3
                # Показываем Paywall (Алерт)
                msg = get_text(lang, "limit_favorites_exceeded") or "🔒 Limit reached. Get Premium."
                await callback.answer(msg, show_alert=True)
                return

        dish_index = int(callback.data.split('_')[2])
        dishes = state_manager.get_generated_dishes(user_id)
        current_dish_state = state_manager.get_current_dish(user_id)
        
        # Надежное определение выбранного блюда
        selected_dish = current_dish_state if current_dish_state else (dishes[dish_index] if dishes else None)
        
        if not selected_dish:
            await callback.answer("Error: Recipe expired. Please generate again.")
            return
            
        dish_name = selected_dish.get('name')
        category_str = state_manager.get_categories(user_id)[0] if state_manager.get_categories(user_id) else 'unknown'
        
        recipe_text = state_manager.get_current_recipe_text(user_id)
        if not recipe_text: recipe_text = f"Recipe: {dish_name}\n(Text lost)"
        
        fav = FavoriteRecipe(
            user_id=user_id, dish_name=dish_name, recipe_text=recipe_text,
            ingredients=state_manager.get_products(user_id) or "",
            language=lang,
            category=Category(category_str) if category_str in Category.__members__ else None
        )
        
        if await favorites_repo.add_favorite(fav):
            await callback.answer(get_text(lang, "favorite_added").format(dish_name=dish_name))
            await update_favorite_button(callback, dish_index, True, lang)
        else: await callback.answer("Database Error")

    except Exception as e:
        logger.error(f"Fav Add Error: {e}", exc_info=True)
        await callback.answer("Error")

async def handle_remove_from_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    try:
        dish_index = int(callback.data.split('_')[2])
        current_dish = state_manager.get_current_dish(user_id)
        
        dish_name = current_dish.get('name') if current_dish else None
        
        if not dish_name:
            await callback.answer("Recipe expired")
            return
        
        if await favorites_repo.remove_favorite(user_id, dish_name):
            await callback.answer(get_text(lang, "favorite_removed").format(dish_name=dish_name))
            await update_favorite_button(callback, dish_index, False, lang)
        else: await callback.answer("Delete Error")
    except Exception as e:
        logger.error(f"Fav Remove Error: {e}")
        await callback.answer("Error")

async def update_favorite_button(callback: CallbackQuery, dish_index: int, is_fav: bool, lang: str):
    """Меняет вид кнопки 'Избранное' без перерисовки всего сообщения"""
    try:
        keyboard = callback.message.reply_markup
        builder = InlineKeyboardBuilder()
        for row in keyboard.inline_keyboard:
            new_row = []
            for btn in row:
                if btn.callback_data and (f"fav_{dish_index}" in btn.callback_data):
                    if is_fav:
                        new_btn = InlineKeyboardButton(text=get_text(lang, "btn_remove_from_fav"), callback_data=f"remove_fav_{dish_index}")
                    else:
                        new_btn = InlineKeyboardButton(text=get_text(lang, "btn_add_to_fav"), callback_data=f"add_fav_{dish_index}")
                    new_row.append(new_btn)
                else: new_row.append(btn)
            builder.row(*new_row)
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    except: pass

def register_favorites_handlers(dp: Dispatcher):
    dp.callback_query.register(handle_favorite_pagination, F.data.startswith("fav_page_"))
    dp.callback_query.register(handle_view_favorite, F.data.startswith("view_fav_"))
    dp.callback_query.register(handle_delete_favorite_by_id, F.data.startswith("delete_fav_id_"))
    dp.callback_query.register(handle_add_to_favorites, F.data.startswith("add_fav_"))
    dp.callback_query.register(handle_remove_from_favorites, F.data.startswith("remove_fav_"))
