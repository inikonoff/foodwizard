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
    
    # Кнопка удаления рецепта и возврата
    if favorites:
        first_fav = favorites[0]
        builder.row(
            InlineKeyboardButton(
                text="??? Удалить этот рецепт",
                callback_data=f"delete_fav_{first_fav['dish_name']}"
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
    await metrics.track_event(user_id, "favorites_page_viewed", {"page": page, "total_pages": total_pages})

async def handle_add_to_favorites(callback: CallbackQuery):
    """Добавляет рецепт в избранное"""
    user_id = callback.from_user.id
    
    # Получаем данные пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Извлекаем данные из callback_data (add_fav_1 -> индекс 1)
    try:
        dish_index = int(callback.data.split('_')[2])
        
        # Получаем текущее блюдо из state_manager
        from state_manager import state_manager
        dish_name = state_manager.get_generated_dish(user_id, dish_index)
        
        if not dish_name:
            await callback.answer("Ошибка: блюдо не найдено")
            return
        
        # Получаем рецепт (нужно сохранить его текст)
        # В реальной реализации здесь нужно получить текст рецепта
        # Для примера создаём фиктивный рецепт
        recipe_text = f"Рецепт для {dish_name}\n\nЭтот рецепт был сохранён в избранное."
        
        # Получаем текущие продукты
        products = state_manager.get_products(user_id) or ""
        
        # Создаём запись в избранном
        from database.models import FavoriteRecipe, Category
        favorite = FavoriteRecipe(
            user_id=user_id,
            dish_name=dish_name,
            recipe_text=recipe_text,
            ingredients=products,
            language=lang
        )
        
        # Сохраняем в базу
        success = await favorites_repo.add_favorite(favorite)
        
        if success:
            await callback.answer(get_text(lang, "recipe_added_to_fav"))
            
            # Логируем добавление в избранное
            await metrics.track_favorite_added(user_id, dish_name, lang)
            
            # Обновляем кнопку (меняем на "в избранном")
            await update_favorite_button(callback, dish_index, True, lang)
        else:
            await callback.answer("? Ошибка при сохранении")
            
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка обработки добавления в избранное: {e}")
        await callback.answer("? Ошибка")

async def handle_remove_from_favorites(callback: CallbackQuery):
    """Удаляет рецепт из избранного"""
    user_id = callback.from_user.id
    
    # Получаем данные пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Извлекаем название блюда из callback_data (remove_fav_pizza_margherita)
    try:
        # callback_data: remove_fav_dishname (dishname может содержать подчёркивания)
        parts = callback.data.split('_')[2:]  # Пропускаем remove_fav
        dish_name = '_'.join(parts)
        
        if not dish_name:
            await callback.answer("Ошибка: название блюда не указано")
            return
        
        # Удаляем из избранного
        success = await favorites_repo.remove_favorite(user_id, dish_name)
        
        if success:
            await callback.answer(get_text(lang, "recipe_removed_from_fav"))
            
            # Логируем удаление из избранного
            await metrics.track_event(user_id, "favorite_removed", {"dish_name": dish_name})
            
            # Обновляем кнопку (меняем на "добавить в избранное")
            # Нужно найти индекс блюда
            from state_manager import state_manager
            dishes = state_manager.get_generated_dishes(user_id)
            for i, dish in enumerate(dishes):
                if dish.get('name') == dish_name:
                    await update_favorite_button(callback, i, False, lang)
                    break
        else:
            await callback.answer("? Ошибка при удалении")
            
    except Exception as e:
        logger.error(f"Ошибка обработки удаления из избранного: {e}")
        await callback.answer("? Ошибка")

async def handle_delete_favorite(callback: CallbackQuery):
    """Удаляет рецепт из избранного (из списка избранного)"""
    user_id = callback.from_user.id
    
    # Получаем данные пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Извлекаем название блюда из callback_data (delete_fav_pizza_margherita)
    try:
        parts = callback.data.split('_')[2:]  # Пропускаем delete_fav
        dish_name = '_'.join(parts)
        
        if not dish_name:
            await callback.answer("Ошибка: название блюда не указано")
            return
        
        # Удаляем из избранного
        success = await favorites_repo.remove_favorite(user_id, dish_name)
        
        if success:
            await callback.answer(get_text(lang, "recipe_removed_from_fav"))
            
            # Обновляем список избранного
            # Просто удаляем сообщение и показываем обновлённый список
            await callback.message.delete()
            
            # Показываем первую страницу избранного
            favorites, total_pages = await favorites_repo.get_favorites_page(user_id, 1)
            
            if not favorites:
                await callback.message.answer(get_text(lang, "favorites_empty"))
                return
            
            # Форматируем список
            recipes_text = ""
            for i, fav in enumerate(favorites, 1):
                date_str = fav['created_at'].strftime("%d.%m.%Y")
                recipes_text += get_text(lang, "favorites_recipe_item", 
                                       num=i, dish=fav['dish_name'], date=date_str)
            
            # Создаём клавиатуру
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
            
            # Логируем удаление
            await metrics.track_event(user_id, "favorite_deleted_from_list", {"dish_name": dish_name})
            
        else:
            await callback.answer("? Ошибка при удалении")
            
    except Exception as e:
        logger.error(f"Ошибка удаления из избранного: {e}")
        await callback.answer("? Ошибка")

async def update_favorite_button(callback: CallbackQuery, dish_index: int, is_favorite: bool, lang: str):
    """Обновляет кнопку избранного в сообщении с рецептом"""
    try:
        # Получаем текущую клавиатуру
        keyboard = callback.message.reply_markup
        
        if not keyboard:
            return
        
        # Создаём новую клавиатуру
        builder = InlineKeyboardBuilder()
        
        # Копируем все строки кнопок, изменяя нужную кнопку
        for row in keyboard.inline_keyboard:
            new_row = []
            for button in row:
                if button.callback_data and f"dish_{dish_index}" in button.callback_data:
                    # Это кнопка блюда, оставляем как есть
                    new_row.append(button)
                elif button.callback_data and ("add_fav" in button.callback_data or "remove_fav" in button.callback_data):
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
                    # Другие кнопки оставляем как есть
                    new_row.append(button)
            
            if new_row:
                builder.row(*new_row)
        
        # Обновляем сообщение
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Ошибка обновления кнопки избранного: {e}")

def register_favorites_handlers(dp: Dispatcher):
    """Регистрирует обработчики для избранного"""
    dp.callback_query.register(handle_favorite_pagination, F.data.startswith("fav_page_"))
    dp.callback_query.register(handle_add_to_favorites, F.data.startswith("add_fav_"))
    dp.callback_query.register(handle_remove_from_favorites, F.data.startswith("remove_fav_"))
    dp.callback_query.register(handle_delete_favorite, F.data.startswith("delete_fav_"))