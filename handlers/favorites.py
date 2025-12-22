import logging
from aiogram import Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from state_manager import state_manager
from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
from config import FAVORITES_PER_PAGE
from database.models import FavoriteRecipe, Category

logger = logging.getLogger(__name__)

async def track_safely(user_id: int, event_name: str, data: dict = None):
    try:
        await metrics.track_event(user_id, event_name, data)
    except Exception as e:
        logger.error(f"❌ Ошибка записи метрики ({event_name}): {e}", exc_info=True)

# --- 1. СПИСОК (Пагинация) ---
async def handle_favorite_pagination(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    
    try:
        page = int(callback.data.split('_')[2])
    except (IndexError, ValueError):
        page = 1
    
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page)
    
    if not favorites:
        # Если список пуст, но мы пытаемся редактировать старое сообщение
        try:
            await callback.message.edit_text(get_text(lang, "favorites_empty"))
        except TelegramBadRequest:
            await callback.message.answer(get_text(lang, "favorites_empty"))
        return 
    
    header_text = get_text(lang, "favorites_title") + f" (стр. {page}/{total_pages})"
    builder = InlineKeyboardBuilder()
    
    for fav in favorites:
        date_str = fav['created_at'].strftime("%d.%m")
        btn_text = f"{fav['dish_name']} ({date_str})"
        builder.row(InlineKeyboardButton(text=btn_text, callback_data=f"view_fav_{fav['id']}"))
    
    if total_pages > 1:
        row = []
        if page > 1: row.append(InlineKeyboardButton(text="⬅️", callback_data=f"fav_page_{page - 1}"))
        row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages: row.append(InlineKeyboardButton(text="➡️", callback_data=f"fav_page_{page + 1}"))
        builder.row(*row)
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await callback.message.edit_text(header_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()
    await track_safely(user_id, "favorites_page_viewed", {"page": page})

# --- 2. ПРОСМОТР РЕЦЕПТА ---
async def handle_view_favorite(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        fav_id = int(callback.data.split('_')[2])
        recipe = await favorites_repo.get_favorite_by_id(fav_id)
        
        if not recipe:
            await callback.answer("Рецепт не найден")
            return

        full_text = f"🍳 <b>{recipe['dish_name']}</b>\n\n{recipe['recipe_text']}\n\n🛒 <i>{recipe.get('ingredients', '')}</i>"
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_fav_id_{fav_id}"))
        builder.row(InlineKeyboardButton(text="🔙 К списку", callback_data="fav_page_1"))
        
        await callback.message.edit_text(full_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await callback.answer()
    except Exception as e:
        logger.error(f"View Error: {e}", exc_info=True)
        await callback.answer("Ошибка")

# --- 3. УДАЛЕНИЕ ПО ID (из списка) ---
async def handle_delete_favorite_by_id(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        fav_id = int(callback.data.split('_')[3])
        fav = await favorites_repo.get_favorite_by_id(fav_id)
        if not fav:
            await callback.answer("Уже удалено")
            await handle_favorite_pagination(callback)
            return

        success = await favorites_repo.remove_favorite(user_id, fav['dish_name'])
        if success:
            await callback.answer("🗑 Рецепт удален")
            callback.data = "fav_page_1" 
            await handle_favorite_pagination(callback)
        else:
            await callback.answer("Ошибка удаления")
    except Exception as e:
        logger.error(f"Del Error: {e}", exc_info=True)
        await callback.answer("Ошибка")

# --- 4. ДОБАВЛЕНИЕ (Кнопка под рецептом) ---
async def handle_add_to_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        # callback: add_fav_1
        dish_index = int(callback.data.split('_')[2])
        
        dishes = state_manager.get_generated_dishes(user_id)
        current_dish_state = state_manager.get_current_dish(user_id)
        
        selected_dish = current_dish_state if current_dish_state else (dishes[dish_index] if dishes else None)
        if not selected_dish:
            await callback.answer("Ошибка: рецепт не найден в памяти")
            return
        
        dish_name = selected_dish.get('name')
        category_str = state_manager.get_categories(user_id)[0] if state_manager.get_categories(user_id) else 'unknown'
        
        recipe_text = state_manager.get_current_recipe_text(user_id)
        if not recipe_text: recipe_text = f"Рецепт: {dish_name}\n(Текст не сохранился)"
        
        favorite = FavoriteRecipe(
            user_id=user_id, dish_name=dish_name, recipe_text=recipe_text,
            ingredients=state_manager.get_products(user_id) or "",
            language=lang, category=Category(category_str) if category_str in Category.__members__ else None
        )
        
        if await favorites_repo.count_favorites(user_id) >= 100:
             await callback.answer(get_text(lang, "favorite_limit").format(limit=100))
             return

        success = await favorites_repo.add_favorite(favorite)
        if success:
            # Уведомление всплывашкой
            await callback.answer(get_text(lang, "favorite_added").format(dish_name=dish_name))
            await track_safely(user_id, "favorite_added", {"dish_name": dish_name})
            
            # ОБНОВЛЕНИЕ КНОПКИ (Переключаем на "В избранном")
            await update_favorite_button(callback, dish_index, is_in_favorites=True, lang=lang)
        else:
            await callback.answer("⚠️ Ошибка")
    except Exception as e:
        logger.error(f"Add Error: {e}", exc_info=True)
        await callback.answer("Ошибка")

# --- 5. УДАЛЕНИЕ (Кнопка под рецептом) ---
async def handle_remove_from_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    try:
        # callback: remove_fav_1
        dish_index = int(callback.data.split('_')[2])
        current_dish = state_manager.get_current_dish(user_id)
        dishes = state_manager.get_generated_dishes(user_id)
        
        dish_name = None
        if current_dish:
            dish_name = current_dish.get('name')
        elif dishes and 0 <= dish_index < len(dishes):
            dish_name = dishes[dish_index].get('name')
        
        if not dish_name:
            await callback.answer("Сессия истекла")
            return
        
        if await favorites_repo.remove_favorite(user_id, dish_name):
            await callback.answer(get_text(lang, "favorite_removed").format(dish_name=dish_name))
            await track_safely(user_id, "favorite_removed", {"dish_name": dish_name})
            
            # ОБНОВЛЕНИЕ КНОПКИ (Переключаем обратно на "В избранное")
            await update_favorite_button(callback, dish_index, is_in_favorites=False, lang=lang)
        else:
            await callback.answer("Ошибка удаления")
    except Exception as e:
        logger.error(f"Remove Error: {e}", exc_info=True)
        await callback.answer("Ошибка")

# --- ФУНКЦИЯ ОБНОВЛЕНИЯ КНОПКИ (КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ) ---
async def update_favorite_button(callback: CallbackQuery, dish_index: int, is_in_favorites: bool, lang: str):
    """
    Меняет кнопку в клавиатуре на лету (тоггл).
    """
    try:
        current_keyboard = callback.message.reply_markup
        if not current_keyboard: return
        
        builder = InlineKeyboardBuilder()
        
        # Пересобираем клавиатуру
        for row in current_keyboard.inline_keyboard:
            new_row = []
            for button in row:
                # Проверяем callback_data. Кнопки выглядят как add_fav_X или remove_fav_X
                # Нам нужно найти ту, которая относится к текущему индексу блюда
                is_target_btn = False
                if button.callback_data:
                    # Проверяем точное совпадение префикса и индекса
                    if button.callback_data == f"add_fav_{dish_index}" or button.callback_data == f"remove_fav_{dish_index}":
                        is_target_btn = True
                
                if is_target_btn:
                    if is_in_favorites:
                        # Ставим кнопку "🌟 В избранном" (нажатие удалит)
                        new_btn = InlineKeyboardButton(
                            text=get_text(lang, "btn_remove_from_fav"), 
                            callback_data=f"remove_fav_{dish_index}"
                        )
                    else:
                        # Ставим кнопку "☆ В избранное" (нажатие добавит)
                        new_btn = InlineKeyboardButton(
                            text=get_text(lang, "btn_add_to_fav"), 
                            callback_data=f"add_fav_{dish_index}"
                        )
                    new_row.append(new_btn)
                else:
                    # Остальные кнопки (Ещё рецепт, Назад) оставляем как есть
                    new_row.append(button)
            builder.row(*new_row)
            
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        
    except TelegramBadRequest as e:
        # Игнорируем ошибку, если сообщение не изменилось (пользователь нажал дважды быстро)
        if "message is not modified" in str(e):
            return
        logger.error(f"Ошибка обновления кнопки: {e}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка обновления кнопки: {e}")

def register_favorites_handlers(dp: Dispatcher):
    dp.callback_query.register(handle_favorite_pagination, F.data.startswith("fav_page_"))
    dp.callback_query.register(handle_view_favorite, F.data.startswith("view_fav_"))
    dp.callback_query.register(handle_delete_favorite_by_id, F.data.startswith("delete_fav_id_"))
    
    # Обработчики для качелей
    dp.callback_query.register(handle_add_to_favorites, F.data.startswith("add_fav_"))
    dp.callback_query.register(handle_remove_from_favorites, F.data.startswith("remove_fav_"))
