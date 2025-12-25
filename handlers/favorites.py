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
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    try: page = int(callback.data.split('_')[2])
    except: page = 1
    
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page)
    if not favorites:
        try: await callback.message.edit_text(get_text(lang, "favorites_empty"))
        except: await callback.message.answer(get_text(lang, "favorites_empty"))
        return 
    
    header = get_text(lang, "favorites_title") + f" ({page}/{total_pages})"
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
    await callback.message.edit_text(header, reply_markup=builder.as_markup(), parse_mode="Markdown")

async def handle_view_favorite(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        fav_id = int(callback.data.split('_')[2])
        recipe = await favorites_repo.get_favorite_by_id(fav_id)
        if not recipe:
            await callback.answer("Рецепт не найден")
            return
        text = f"🍳 <b>{recipe['dish_name']}</b>\n\n{recipe['recipe_text']}\n\n🛒 <i>{recipe.get('ingredients', '')}</i>"
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_fav_id_{fav_id}"))
        builder.row(InlineKeyboardButton(text="🔙 К списку", callback_data="fav_page_1"))
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    except: await callback.answer("Ошибка")

async def handle_delete_favorite_by_id(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        fav_id = int(callback.data.split('_')[3])
        fav = await favorites_repo.get_favorite_by_id(fav_id)
        if fav and await favorites_repo.remove_favorite(user_id, fav['dish_name']):
            await callback.answer("Удалено")
            callback.data = "fav_page_1"
            await handle_favorite_pagination(callback)
        else: await callback.answer("Ошибка")
    except: await callback.answer("Ошибка")

# --- ДОБАВЛЕНИЕ С МЯГКИМ ЛИМИТОМ ---
async def handle_add_to_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru')
    is_premium = user_data.get('is_premium', False)

    try:
        # Проверка лимита для Free (мягкая монетизация)
        if not is_premium:
            current_count = await favorites_repo.count_favorites(user_id)
            if current_count >= FREE_USER_LIMITS["max_favorites"]:
                await callback.answer(get_text(lang, "limit_favorites_exceeded"), show_alert=True)
                return

        dish_index = int(callback.data.split('_')[2])
        dishes = state_manager.get_generated_dishes(user_id)
        current = state_manager.get_current_dish(user_id)
        selected = current if current else (dishes[dish_index] if dishes else None)
        
        if not selected:
            await callback.answer("Ошибка данных")
            return
            
        dish_name = selected.get('name')
        text = state_manager.get_current_recipe_text(user_id) or f"Рецепт: {dish_name}"
        
        fav = FavoriteRecipe(
            user_id=user_id, dish_name=dish_name, recipe_text=text,
            ingredients=state_manager.get_products(user_id) or "",
            language=lang
        )
        
        if await favorites_repo.add_favorite(fav):
            await callback.answer(get_text(lang, "favorite_added").format(dish_name=dish_name))
            await update_favorite_button(callback, dish_index, True, lang)
        else: await callback.answer("Ошибка")
    except: await callback.answer("Ошибка")

async def handle_remove_from_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    try:
        dish_index = int(callback.data.split('_')[2])
        dishes = state_manager.get_generated_dishes(user_id)
        current = state_manager.get_current_dish(user_id)
        dish_name = current.get('name') if current else (dishes[dish_index].get('name') if dishes else None)
        
        if dish_name and await favorites_repo.remove_favorite(user_id, dish_name):
            await callback.answer(get_text(lang, "favorite_removed").format(dish_name=dish_name))
            await update_favorite_button(callback, dish_index, False, lang)
        else: await callback.answer("Ошибка")
    except: await callback.answer("Ошибка")

async def update_favorite_button(callback: CallbackQuery, dish_index: int, is_fav: bool, lang: str):
    try:
        keyboard = callback.message.reply_markup
        builder = InlineKeyboardBuilder()
        for row in keyboard.inline_keyboard:
            new_row = []
            for btn in row:
                if btn.callback_data and (f"fav_{dish_index}" in btn.callback_data):
                    if is_fav: new_btn = InlineKeyboardButton(text=get_text(lang, "btn_remove_from_fav"), callback_data=f"remove_fav_{dish_index}")
                    else: new_btn = InlineKeyboardButton(text=get_text(lang, "btn_add_to_fav"), callback_data=f"add_fav_{dish_index}")
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