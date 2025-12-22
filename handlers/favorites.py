import logging
from aiogram import Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from state_manager import state_manager
from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
from config import FAVORITES_PER_PAGE
from database.models import FavoriteRecipe, Category

logger = logging.getLogger(__name__)

# --- Вспомогательная функция ---
async def track_safely(user_id: int, event_name: str, data: dict = None):
    try:
        await metrics.track_event(user_id, event_name, data)
    except Exception as e:
        logger.error(f"❌ Ошибка записи метрики ({event_name}): {e}", exc_info=True)


# 1. Функция пагинации
async def handle_favorite_pagination(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        page = int(callback.data.split('_')[2])
    except (IndexError, ValueError):
        page = 1
    
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page)
    
    if not favorites:
        await callback.message.edit_text(get_text(lang, "favorites_empty"))
        await callback.answer()
        return
    
    recipes_text = ""
    for i, fav in enumerate(favorites, 1):
        item_num = (page - 1) * FAVORITES_PER_PAGE + i
        date_str = fav['created_at'].strftime("%d.%m.%Y")
        recipes_text += get_text(lang, "favorites_recipe_item", 
                               num=item_num, dish=fav['dish_name'], date=date_str)
    
    builder = InlineKeyboardBuilder()
    
    if total_pages > 1:
        buttons = []
        if page > 1:
            buttons.append(InlineKeyboardButton(text=get_text(lang, "btn_prev"), callback_data=f"fav_page_{page - 1}"))
        buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            buttons.append(InlineKeyboardButton(text=get_text(lang, "btn_next"), callback_data=f"fav_page_{page + 1}"))
        builder.row(*buttons)
    
    if favorites:
        first_fav = favorites[0]
        safe_dish_name = first_fav['dish_name'].replace(' ', '_')
        builder.row(InlineKeyboardButton(text="🗑 Удалить первый рецепт", callback_data=f"delete_fav_{safe_dish_name}"))
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    text = get_text(lang, "favorites_list", page=page, total_pages=total_pages, recipes=recipes_text)
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()
    await track_safely(user_id, "favorites_page_viewed", {"page": page, "total_pages": total_pages})


# 2. Функция добавления (ВНИМАНИЕ: имя handle_add_TO_favorites)
async def handle_add_to_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        dish_index = int(callback.data.split('_')[2])
        dishes = state_manager.get_generated_dishes(user_id)
        current_dish_state = state_manager.get_current_dish(user_id)
        
        selected_dish = None
        if current_dish_state:
            selected_dish = current_dish_state
        elif dishes and 0 <= dish_index < len(dishes):
            selected_dish = dishes[dish_index]
            
        if not selected_dish:
            await callback.answer("Ошибка: блюдо не найдено или сессия истекла")
            return
        
        dish_name = selected_dish.get('name')
        categories = state_manager.get_categories(user_id)
        category_str = categories[0] if categories else 'unknown'
        
        recipe_text = f"Рецепт: {dish_name}\n(Сохранен из истории)"
        products = state_manager.get_products(user_id) or ""
        
        favorite = FavoriteRecipe(
            user_id=user_id,
            dish_name=dish_name,
            recipe_text=recipe_text,
            ingredients=products,
            language=lang,
            category=Category(category_str) if category_str in Category.__members__ else None
        )
        
        success = await favorites_repo.add_favorite(favorite)
        
        if success:
            await callback.answer(get_text(lang, "favorite_added").format(dish_name=dish_name))
            await track_safely(user_id, "favorite_added", {"dish_name": dish_name})
            await update_favorite_button(callback, dish_index, True, lang)
        else:
            await callback.answer("⚠️ Ошибка при сохранении")
            
    except Exception as e:
        logger.error(f"Ошибка добавления в избранное: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка")


# 3. Функция удаления из карточки (ВНИМАНИЕ: имя handle_remove_FROM_favorites)
async def handle_remove_from_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        dish_index = int(callback.data.split('_')[2])
        dishes = state_manager.get_generated_dishes(user_id)
        
        dish_name = None
        if dishes and 0 <= dish_index < len(dishes):
            dish_name = dishes[dish_index].get('name')
            
        if not dish_name:
            await callback.answer("Сессия истекла")
            return
        
        success = await favorites_repo.remove_favorite(user_id, dish_name)
        
        if success:
            await callback.answer(get_text(lang, "favorite_removed").format(dish_name=dish_name))
            await track_safely(user_id, "favorite_removed", {"dish_name": dish_name})
            await update_favorite_button(callback, dish_index, False, lang)
        else:
            await callback.answer("⚠️ Ошибка при удалении")
            
    except Exception as e:
        logger.error(f"Ошибка удаления из избранного: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка")


# 4. Функция удаления из списка
async def handle_delete_favorite(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        dish_name_part = callback.data.split('_', 2)[-1]
        dish_name = dish_name_part.replace('_', ' ')
        
        success = await favorites_repo.remove_favorite(user_id, dish_name)
        
        if success:
            await callback.answer(get_text(lang, "favorite_removed").format(dish_name=dish_name))
            await callback.message.delete()
            favorites, total_pages = await favorites_repo.get_favorites_page(user_id, 1)
            
            if not favorites:
                await callback.message.answer(get_text(lang, "favorites_empty"))
                return
            
            recipes_text = ""
            for i, fav in enumerate(favorites, 1):
                date_str = fav['created_at'].strftime("%d.%m.%Y")
                recipes_text += get_text(lang, "favorites_recipe_item", num=i, dish=fav['dish_name'], date=date_str)
            
            builder = InlineKeyboardBuilder()
            if total_pages > 1:
                builder.row(InlineKeyboardButton(text=get_text(lang, "btn_prev"), callback_data="fav_page_1"),
                            InlineKeyboardButton(text=f"1/{total_pages}", callback_data="noop"),
                            InlineKeyboardButton(text=get_text(lang, "btn_next"), callback_data="fav_page_2"))
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
            
            text = get_text(lang, "favorites_list", page=1, total_pages=total_pages, recipes=recipes_text)
            await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
            await track_safely(user_id, "favorite_deleted_from_list", {"dish_name": dish_name})
        else:
            await callback.answer("⚠️ Не удалось удалить")
            
    except Exception as e:
        logger.error(f"Ошибка удаления из списка: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка")


# 5. Функция обновления кнопок
a
