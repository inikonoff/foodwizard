import logging
from aiogram import Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импорты ваших модулей
from state_manager import state_manager
from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
from config import FAVORITES_PER_PAGE
from database.models import FavoriteRecipe, Category

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
    
    # Получаем данные пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Извлекаем номер страницы из callback_data (fav_page_1 -> 1)
    try:
        page = int(callback.data.split('_')[2])
    except (IndexError, ValueError):
        page = 1
    
    # Получаем избранные рецепты для страницы
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page)
    
    if not favorites:
        await callback.message.edit_text(get_text(lang, "favorites_empty"))
        await callback.answer()
        return
    
    # Форматируем список рецептов
    recipes_text = ""
    for i, fav in enumerate(favorites, 1):
        # Вычисляем номер на странице
        item_num = (page - 1) * FAVORITES_PER_PAGE + i
        date_str = fav['created_at'].strftime("%d.%m.%Y")
        recipes_text += get_text(lang, "favorites_recipe_item", 
                               num=item_num, dish=fav['dish_name'], date=date_str)
    
    # Создаём клавиатуру с пагинацией
    builder = InlineKeyboardBuilder()
    
    # Кнопки пагинации (только если больше одной страницы)
    if total_pages > 1:
        buttons = []
        
        # Кнопка "назад"
        if page > 1:
            buttons.append(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_prev"),
                    callback_data=f"fav_page_{page - 1}"
                )
            )
        
        # Номер страницы
        buttons.append(
            InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data="noop"
            )
        )
        
        # Кнопка "вперёд"
        if page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_next"),
                    callback_data=f"fav_page_{page + 1}"
                )
            )
        
        builder.row(*buttons)
    
    # Кнопка удаления первого рецепта (как пример функционала)
    if favorites:
        first_fav = favorites[0]
        # Заменяем пробелы на подчеркивания для безопасности callback_data
        safe_dish_name = first_fav['dish_name'].replace(' ', '_')
        builder.row(
            InlineKeyboardButton(
                text="🗑 Удалить первый рецепт",
                callback_data=f"delete_fav_{safe_dish_name}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    # Отправляем обновлённое сообщение
    text = get_text(lang, "favorites_list", page=page, total_pages=total_pages, recipes=recipes_text)
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()
    
    # Логируем просмотр страницы
    await track_safely(user_id, "favorites_page_viewed", {"page": page, "total_pages": total_pages})


async def handle_add_to_favorites(callback: CallbackQuery):
    """Добавляет рецепт в избранное (кнопка под сгенерированным рецептом)"""
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        # Извлекаем индекс из callback_data (add_fav_1 -> индекс 1)
        dish_index = int(callback.data.split('_')[2])
        
        # Получаем список сгенерированных блюд из состояния
        dishes = state_manager.get_generated_dishes(user_id)
        current_dish_state = state_manager.get_current_dish(user_id)
        
        # Определяем текущее блюдо
        selected_dish = None
        if current_dish_state:
            selected_dish = current_dish_state
        elif dishes and 0 <= dish_index < len(dishes):
            selected_dish = dishes[dish_index]
            
        if not selected_dish:
            await callback.answer("Ошибка: блюдо не найдено или сессия истекла")
            return
        
        dish_name = selected_dish.get('name')
        
        # Получаем категорию
        categories = state_manager.get_categories(user_id)
        category_str = categories[0] if categories else 'unknown'
        
        # Формируем текст (в реальном проекте лучше хранить полный текст в state_manager)
        recipe_text = f"Рецепт: {dish_name}\n(Сохранен из истории)"
        products = state_manager.get_products(user_id) or ""
        
        # Создаём объект для БД
        favorite = FavoriteRecipe(
            user_id=user_id,
            dish_name=dish_name,
            recipe_text=recipe_text,
            ingredients=products,
            language=lang,
            category=Category(category_str) if category_str in Category.__members__ else None
        )
        
        # Сохраняем в базу
        success = await favorites_repo.add_favorite(favorite)
        
        if success:
            await callback.answer(get_text(lang, "favorite_added").format(dish_name=dish_name))
            
            # Логируем
            await track_safely(user_id, "favorite_added", {"dish_name": dish_name})
            
            # Обновляем кнопку на "Удалить из избранного"
            await update_favorite_button(callback, dish_index, True, lang)
        else:
            await callback.answer("⚠️ Ошибка при сохранении")
            
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка обработки добавления в избранное: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка данных")


async def handle_remove_from_favorites(callback: CallbackQuery):
    """Удаляет рецепт из избранного (кнопка под сгенерированным рецептом)"""
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        dish_index = int(callback.data.split('_')[2])
        
        # Пытаемся найти имя блюда через state_manager
        dishes = state_manager.get_generated_dishes(user_id)
        dish_name = None
        
        if dishes and 0 <= dish_index < len(dishes):
            dish_name = dishes[dish_index].get('name')
            
        if not dish_name:
            # Если сессия истекла, мы не можем узнать имя блюда для удаления по индексу
            await callback.answer("Сессия истекла, невозможно удалить")
            return
        
        # Удаляем из БД
        success = await favorites_repo.remove_favorite(user_id, dish_name)
        
        if success:
            await callback.answer(get_text(lang, "favorite_removed").format(dish_name=dish_name))
            
            await track_safely(user_id, "favorite_removed", {"dish_name": dish_name})
            
            # Обновляем кнопку обратно на "Добавить"
            await update_favorite_button(callback, dish_index, False, lang)
        else:
            await callback.answer("⚠️ Ошибка при удалении")
            
    except Exception as e:
        logger.error(f"Ошибка удаления из избранного: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка")


async def handle_delete_favorite(callback: CallbackQuery):
    """Удаляет рецепт из списка избранного (из меню /favorites)"""
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        # Извлекаем имя блюда. Формат: delete_fav_Dish_Name
        # Восстанавливаем пробелы из подчеркиваний
        dish_name_part = callback.data.split('_', 2)[-1]
        dish_name = dish_name_part.replace('_', ' ')
        
        if not dish_name:
            await callback.answer("Ошибка имени блюда")
            return
        
        success = await favorites_repo.remove_favorite(user_id, dish_name)
        
        if success:
            await callback.answer(get_text(lang, "favorite_removed").format(dish_name=dish_name))
            
            # Обновляем список (просто удаляем сообщение и показываем заново 1 страницу)
            await callback.message.delete()
            
            # Показываем список заново
            favorites, total_pages = await favorites_repo.get_favorites_page(user_id, 1)
            
            if not favorites:
                await callback.message.answer(get_text(lang, "favorites_empty"))
                return
            
            # Формируем текст (дублирование логики для простоты)
            recipes_text = ""
            for i, fav in enumerate(favorites, 1):
                date_str = fav['created_at'].strftime("%d.%m.%Y")
                recipes_text += get_text(lang, "favorites_recipe_item", num=i, dish=fav['dish_name'], date=date_str)
            
            builder = InlineKeyboardBuilder()
            if total_pages > 1:
                builder.row(
                    InlineKeyboardButton(text=get_text(lang, "btn_prev"), callback_data="fav_page_1"),
                    InlineKeyboardButton(text=f"1/{total_pages}", callback_data="noop"),
                    InlineKeyboardButton(text=get_text(lang, "btn_next"), callback_data="fav_page_2")
                )
            builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
            
            text = get_text(lang, "favorites_list", page=1, total_pages=total_pages, recipes=recipes_text)
            await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
            
            await track_safely(user_id, "favorite_deleted_from_list", {"dish_name": dish_name})
        else:
            await callback.answer("⚠️ Не удалось удалить")
            
    except Exception as e:
        logger.error(f"Ошибка удаления из списка: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка")


async def update_favorite_button(callback: CallbackQuery, dish_index: int, is_favorite: bool, lang: str):
    """Обновляет клавиатуру сообщения, меняя кнопку добавления/удаления"""
    try:
        keyboard = callback.message.reply_markup
        if not keyboard: return
        
        builder = InlineKeyboardBuilder()
        
        for row in keyboard.inline_keyboard:
            new_row = []
            for button in row:
                # Ищем кнопку избранного (add_fav или remove_fav)
                if button.callback_data and ("add_fav" in button.callback_data or "remove_fav" in button.callback_data):
                    if is_favorite:
                        new_btn = InlineKeyboardButton(
                            text=get_text(lang, "btn_remove_from_fav"),
                            callback_data=f"remove_fav_{dish_index}"
                        )
                    else:
                        new_btn = InlineKeyboardButton(
                            text=get_text(lang, "btn_add_to_fav"),
                            callback_data=f"add_fav_{dish_index}"
                        )
                    new_row.append(new_btn)
                else:
                    new_row.append(button)
            builder.row(*new_row)
            
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    except Exception as e:
        logger.error(f"Ошибка обновления кнопки: {e}")


def register_favorites_handlers(dp: Dispatcher):
    """Регистрирует обработчики для избранного"""
    # 1. Пагинация
    dp.callback_query.register(handle_favorite_pagination, F.data.startswith("fav_page_"))
    
    # 2. Добавление (ИМЯ ФУНКЦИИ: handle_add_to_favorites)
    dp.callback_query.register(handle_add_to_favorites, F.data.startswith("add_fav_"))
    
    # 3. Удаление из карточки (ИМЯ ФУНКЦИИ: handle_remove_from_favorites)
    dp.callback_query.register(handle_remove_from_favorites, F.data.startswith("remove_fav_"))
    
    # 4. Удаление из списка
    dp.callback_query.register(handle_delete_favorite, F.data.startswith("delete_fav_"))
