import logging
from typing import List, Optional, Dict, Any, Tuple
from aiogram import Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from state_manager import state_manager
from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
from config import FAVORITES_PER_PAGE
from database.models import FavoriteRecipe, Category # Добавил явный импорт

logger = logging.getLogger(__name__)

# --- Вспомогательная функция для безопасного логирования метрик ---
async def track_safely(user_id: int, event_name: str, data: dict = None):
    """Оборачивает логирование метрик в try/except"""
    try:
        await metrics.track_event(user_id, event_name, data)
    except Exception as e:
        logger.error(f"❌ Ошибка записи метрики ({event_name}): {e}", exc_info=True)


async def handle_favorite_pagination(callback: CallbackQuery):
    """Обрабатывает пагинацию в избранном"""
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
    
    # Форматируем список рецептов
    recipes_text = ""
    for i, fav in enumerate(favorites, 1):
        item_num = (page - 1) * FAVORITES_PER_PAGE + i
        date_str = fav['created_at'].strftime("%d.%m.%Y")
        recipes_text += get_text(lang, "favorites_recipe_item", 
                               num=item_num, dish=fav['dish_name'], date=date_str)
    
    builder = InlineKeyboardBuilder()
    
    # Кнопки пагинации
    if total_pages > 1:
        buttons = []
        
        if page > 1:
            buttons.append(InlineKeyboardButton(text=get_text(lang, "btn_prev"), callback_data=f"fav_page_{page - 1}"))
        
        buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        
        if page < total_pages:
            buttons.append(InlineKeyboardButton(text=get_text(lang, "btn_next"), callback_data=f"fav_page_{page + 1}"))
        
        builder.row(*buttons)
    
    # Кнопка удаления рецепта и возврата
    if favorites:
        first_fav = favorites[0]
        # ВАЖНО: Передаем имя блюда, заменяя пробелы на подчеркивание для безопасности коллбэка
        safe_dish_name = first_fav['dish_name'].replace(' ', '_')
        builder.row(
            InlineKeyboardButton(
                text="??? Удалить этот рецепт",
                callback_data=f"delete_fav_{safe_dish_name}"
            )
        )
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    text = get_text(lang, "favorites_list", page=page, total_pages=total_pages, recipes=recipes_text)
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()
    
    await track_safely(user_id, "favorites_page_viewed", {"page": page, "total_pages": total_pages})

async def handle_add_to_favorites(callback: CallbackQuery):
    """Добавляет рецепт в избранное"""
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        dish_index = int(callback.data.split('_')[2])
        
        # --- КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ПРАВИЛЬНОЕ ПОЛУЧЕНИЕ ИМЕНИ БЛЮДА ---
        dishes = state_manager.get_generated_dishes(user_id)
        current_dish_state = state_manager.get_current_dish(user_id) # Используем текущее блюдо, если оно сохранено
        
        if not current_dish_state and (not dishes or dish_index < 0 or dish_index >= len(dishes)):
            await callback.answer("Ошибка: блюдо не найдено или сессия истекла")
            return

        # Используем текущее блюдо, которое только что было сгенерировано (если оно есть)
        selected_dish = current_dish_state if current_dish_state else dishes[dish_index]
        dish_name = selected_dish.get('name')
        category = selected_dish.get('category') or state_manager.get_categories(user_id)[0] if state_manager.get_categories(user_id) else 'unknown'

        # ВАЖНО: В реальном проекте полный текст рецепта должен быть сохранен в state_manager.
        recipe_text = f"Рецепт для {dish_name} (Текст не сохранен в сессии)" 
        products = state_manager.get_products(user_id) or ""
        
        # Создаём запись в избранном
        favorite = FavoriteRecipe(
            user_id=user_id,
            dish_name=dish_name,
            recipe_text=recipe_text,
            ingredients=products,
            language=lang,
            category=Category(category) # Преобразуем str в Enum (Category)
        )
        
        # Проверяем лимит избранного
        if await favorites_repo.count_favorites(user_id) >= 100: # Заглушка лимита
             await callback.answer(get_text(lang, "favorite_limit").format(limit=100))
             return

        # Сохраняем в базу
        success = await favorites_repo.add_favorite(favorite)
        
        if success:
            await callback.answer(get_text(lang, "favorite_added").format(dish_name=dish_name))
            
            await track_safely(user_id, "favorite_added", {"dish_name": dish_name, "lang": lang})
            
            # Обновляем кнопку (меняем на "в избранном")
            await update_favorite_button(callback, dish_index, True, lang)
        else:
            await callback.answer("? Ошибка при сохранении")
            
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка обработки добавления в избранное: {e}", exc_info=True)
        await callback.answer("? Ошибка")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка добавления в избранное: {e}", exc_info=True)
        await callback.answer("? Непредвиденная ошибка")


async def handle_remove_from_favorites(callback: CallbackQuery):
    """Удаляет рецепт из избранного (из сообщения с рецептом)"""
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        # Извлекаем данные из callback_data: remove_fav_123 (индекс блюда в текущей сессии)
        dish_index = int(callback.data.split('_')[2])
        dishes = state_manager.get_generated_dishes(user_id)

        # Логика получения имени блюда
        if not dishes or dish_index < 0 or dish_index >= len(dishes):
            await callback.answer("Ошибка: блюдо не найдено или сессия истекла")
            return
            
        dish_name = dishes[dish_index].get('name')
        
        # Удаляем из избранного
        success = await favorites_repo.remove_favorite(user_id, dish_name)
        
        if success:
            await callback.answer(get_text(lang, "favorite_removed").format(dish_name=dish_name))
            
            await track_safely(user_id, "favorite_removed", {"dish_name": dish_name})
            
            # Обновляем кнопку (меняем на "добавить в избранное")
            await update_favorite_button(callback, dish_index, False, lang)
        else:
            await callback.answer("? Ошибка при удалении")
            
    except Exception as e:
        logger.error(f"Ошибка обработки удаления из избранного: {e}", exc_info=True)
        await callback.answer("? Ошибка")

async def handle_delete_favorite(callback: CallbackQuery):
    """Удаляет рецепт из избранного (из списка избранного)"""
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        # Извлекаем название блюда из callback_data: delete_fav_Пицца_Маргарита
        # !!! Здесь критически важно, чтобы имя блюда совпадало с тем, что в БД !!!
        dish_name = callback.data.split('_', 2)[-1].replace('_', ' ') # Восстанавливаем пробелы
        
        if not dish_name:
            await callback.answer("Ошибка: название блюда не указано")
            return
        
        # Удаляем из избранного
        success = await favorites_repo.remove_favorite(user_id, dish_name)
        
        if success:
            await callback.answer(get_text(lang, "favorite_removed").format(dish_name=dish_name))
            
            # ... (обновляем список избранного, как в вашем коде)
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
            # ... (код пагинации) ...
            
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
            
            text = get_text(lang, "favorites_list", page=1, total_pages=total_pages, recipes=recipes_text)
            await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
            
            await track_safely(user_id, "favorite_deleted_from_list", {"dish_name": dish_name})
            
        else:
            await callback.answer("? Ошибка при удалении")
            
    except Exception as e:
        logger.error(f"Ошибка удаления из избранного: {e}", exc_info=True)
        await callback.answer("? Ошибка")

async def update_favorite_button(callback: CallbackQuery, dish_index: int, is_favorite: bool, lang: str):
    # ... (код обновления кнопки, как в вашем файле) ...
    try:
        keyboard = callback.message.reply_markup
        if not keyboard: return
        builder = InlineKeyboardBuilder()
        for row in keyboard.inline_keyboard:
            new_row = []
            for button in row:
                if button.callback_data and ("add_fav" in button.callback_data or "remove_fav" in button.callback_data):
                    # Это кнопка избранного, обновляем её
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
                    new_row.append(button)
            if new_row:
                builder.row(*new_row)
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    except Exception as e:
        logger.error(f"Ошибка обновления кнопки избранного: {e}", exc_info=True)


# ... (весь предыдущий код handlers/favorites.py) ...

# --- РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ---
def register_favorites_handlers(dp: Dispatcher):
    """Регистрирует обработчики для избранного"""
    # 1. Пагинация
    dp.callback_query.register(handle_favorite_pagination, F.data.startswith("fav_page_"))
    
    # 2. Добавление (Имя функции должно совпадать с def handle_add_to_favorites)
    dp.callback_query.register(handle_add_to_favorites, F.data.startswith("add_fav_"))
    
    # 3. Удаление из карточки (Имя функции должно совпадать с def handle_remove_from_favorites)
    dp.callback_query.register(handle_remove_from_favorites, F.data.startswith("remove_fav_"))
    
    # 4. Удаление из списка
    dp.callback_query.register(handle_delete_favorite, F.data.startswith("delete_fav_"))
