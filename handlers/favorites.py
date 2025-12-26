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

# ... (track_safely, pagination, view, delete, update_button, remove_from - КАК И РАНЬШЕ) ...
# Я приведу только handle_add_to_favorites и важные части

async def handle_favorite_pagination(callback: CallbackQuery):
    # ...
    # 1. Попытка парсинга
    page = 1
    parts = callback.data.split('_')
    # "show_favorites" -> len=2, index 2 fail.
    # "fav_page_2" -> len=3.
    if len(parts) >= 3 and parts[2].isdigit():
        page = int(parts[2])
    favorites, total = await favorites_repo.get_favorites_page(user_id, page)
    if not favorites:
        await callback.message.edit_text(get_text(lang, "favorites_empty"))
        return 
    header = get_text(lang, "favorites_title") + f" ({page}/{total})"
    builder = InlineKeyboardBuilder()
    for fav in favorites:
        btn = f"{fav['dish_name']} ({fav['created_at'].strftime('%d.%m')})"
        builder.row(InlineKeyboardButton(text=btn, callback_data=f"view_fav_{fav['id']}"))
    if total > 1:
        r = []
        if page > 1: r.append(InlineKeyboardButton(text="⬅️", callback_data=f"fav_page_{page-1}"))
        r.append(InlineKeyboardButton(text=f"{page}/{total}", callback_data="noop"))
        if page < total: r.append(InlineKeyboardButton(text="➡️", callback_data=f"fav_page_{page+1}"))
        builder.row(*r)
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await callback.message.edit_text(header, reply_markup=builder.as_markup(), parse_mode="Markdown")

async def handle_view_favorite(c): 
    # Копировать из предыдущих ответов
    user_id = c.from_user.id
    fav_id = int(c.data.split('_')[2])
    recipe = await favorites_repo.get_favorite_by_id(fav_id)
    if recipe:
        text = f"🍳 <b>{recipe['dish_name']}</b>\n\n{recipe['recipe_text']}\n\n🛒 <i>{recipe.get('ingredients','')}</i>"
        b = InlineKeyboardBuilder()
        b.row(InlineKeyboardButton(text="🗑", callback_data=f"delete_fav_id_{fav_id}"))
        b.row(InlineKeyboardButton(text="🔙", callback_data="fav_page_1"))
        await c.message.edit_text(text, reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_delete_favorite_by_id(c):
    # Копировать из предыдущих ответов (удаление по ID)
    try:
        user_id = c.from_user.id
        fav_id = int(c.data.split('_')[3])
        fav = await favorites_repo.get_favorite_by_id(fav_id)
        if fav:
            await favorites_repo.remove_favorite(user_id, fav['dish_name'])
            await c.answer("Deleted")
            c.data = "fav_page_1"
            await handle_favorite_pagination(c)
    except: await c.answer("Error")

async def update_favorite_button(callback: CallbackQuery, dish_index: int, is_in_favorites: bool, lang: str):
    try:
        current_keyboard = callback.message.reply_markup
        if not current_keyboard: return
        builder = InlineKeyboardBuilder()
        for row in current_keyboard.inline_keyboard:
            new_row = []
            for button in row:
                if button.callback_data and (f"add_fav_{dish_index}" in button.callback_data or f"remove_fav_{dish_index}" in button.callback_data):
                    if is_in_favorites:
                        new_btn = InlineKeyboardButton(text=get_text(lang, "btn_remove_from_fav"), callback_data=f"remove_fav_{dish_index}")
                    else:
                        new_btn = InlineKeyboardButton(text=get_text(lang, "btn_add_to_fav"), callback_data=f"add_fav_{dish_index}")
                    new_row.append(new_btn)
                else:
                    new_row.append(button)
            builder.row(*new_row)
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    except: pass

async def handle_remove_from_favorites(c):
    # Стандартная логика удаления с обновлением кнопки
    user_id = c.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    dish_index = int(c.data.split('_')[2])
    cur = state_manager.get_current_dish(user_id)
    # Если это текущий - берем его, иначе ищем в списке
    dish = cur if cur else (state_manager.get_generated_dishes(user_id)[dish_index] if state_manager.get_generated_dishes(user_id) else None)
    
    if dish and await favorites_repo.remove_favorite(user_id, dish['name']):
        await c.answer(get_text(lang, "favorite_removed").format(dish_name=dish['name']))
        await update_favorite_button(c, dish_index, False, lang)
    else: await c.answer("Error")

# --- ДОБАВЛЕНИЕ (FIX "Dish not found") ---
async def handle_add_to_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    if not user_data.get('is_premium', False):
        curr = await favorites_repo.count_favorites(user_id)
        if curr >= FREE_USER_LIMITS["max_favorites"]:
            await callback.answer(get_text(lang, "limit_favorites_exceeded"), show_alert=True)
            return

    try:
        dish_index = int(callback.data.split('_')[2])
        
        # !!! FIX ЛОГИКИ !!!
        # 1. Сначала пробуем взять ТЕКУЩЕЕ блюдо (оно точно установлено в recipes.py)
        selected_dish = state_manager.get_current_dish(user_id)
        
        # 2. Если вдруг нет - пробуем по индексу из списка
        if not selected_dish:
            dishes = state_manager.get_generated_dishes(user_id)
            if dishes and 0 <= dish_index < len(dishes):
                selected_dish = dishes[dish_index]
        
        if not selected_dish:
            await callback.answer("Error: Dish not found in memory (Restart needed)")
            return
            
        dish_name = selected_dish.get('name')
        # Если категорий нет (прямой запрос) - unknown
        cat_list = state_manager.get_categories(user_id)
        cat = cat_list[0] if cat_list else 'unknown'
        
        # Берем сохраненный текст
        txt = state_manager.get_current_recipe_text(user_id)
        if not txt: txt = f"{dish_name}\n(Recipe text lost)"

        fav = FavoriteRecipe(
            user_id=user_id, dish_name=dish_name, recipe_text=txt,
            ingredients=state_manager.get_products(user_id) or "",
            language=lang, category=Category(cat) if cat in Category.__members__ else None
        )
        
        if await favorites_repo.add_favorite(fav):
            await callback.answer(get_text(lang, "favorite_added").format(dish_name=dish_name))
            await update_favorite_button(callback, dish_index, True, lang)
        else: await callback.answer("DB Error")

    except Exception as e:
        logger.error(f"Fav Add Error: {e}", exc_info=True)
        await callback.answer("Error")

def register_favorites_handlers(dp: Dispatcher):
    dp.callback_query.register(handle_favorite_pagination, F.data.startswith("fav_page_"))
    dp.callback_query.register(handle_view_favorite, F.data.startswith("view_fav_"))
    dp.callback_query.register(handle_delete_favorite_by_id, F.data.startswith("delete_fav_id_"))
    dp.callback_query.register(handle_add_to_favorites, F.data.startswith("add_fav_"))
    dp.callback_query.register(handle_remove_from_favorites, F.data.startswith("remove_fav_"))