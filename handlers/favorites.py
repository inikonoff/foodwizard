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


# --- 1. ОТОБРАЖЕНИЕ СПИСКА (КНОПКАМИ) ---
async def handle_favorite_pagination(callback: CallbackQuery):
    """Показывает список избранного (кнопками)"""
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    
    try:
        # Парсим номер страницы (fav_page_1)
        page = int(callback.data.split('_')[2])
    except (IndexError, ValueError):
        page = 1
    
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page)
    
    if not favorites:
        await callback.message.edit_text(get_text(lang, "favorites_empty"))
        return # Важно не отвечать callback.answer, если мы редактируем текст
    
    # Текст заголовка
    header_text = get_text(lang, "favorites_title") + f" (стр. {page}/{total_pages})"
    
    builder = InlineKeyboardBuilder()
    
    # === ГЕНЕРАЦИЯ КНОПОК РЕЦЕПТОВ ===
    for fav in favorites:
        # На кнопке: "Блюдо (Дата)"
        date_str = fav['created_at'].strftime("%d.%m")
        btn_text = f"{fav['dish_name']} ({date_str})"
        
        # Callback: view_fav_ID
        builder.row(InlineKeyboardButton(
            text=btn_text, 
            callback_data=f"view_fav_{fav['id']}"
        ))
    
    # === КНОПКИ ПАГИНАЦИИ ===
    if total_pages > 1:
        pagination_row = []
        if page > 1:
            pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"fav_page_{page - 1}"))
        
        pagination_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        
        if page < total_pages:
            pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"fav_page_{page + 1}"))
        
        builder.row(*pagination_row)
    
    # Кнопка назад в меню
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await callback.message.edit_text(header_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()
    
    await track_safely(user_id, "favorites_page_viewed", {"page": page})


# --- 2. ПРОСМОТР КОНКРЕТНОГО РЕЦЕПТА ---
async def handle_view_favorite(callback: CallbackQuery):
    """Показывает текст рецепта при клике на кнопку"""
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    
    try:
        # view_fav_123 -> id = 123
        fav_id = int(callback.data.split('_')[2])
        
        recipe = await favorites_repo.get_favorite_by_id(fav_id)
        
        if not recipe:
            await callback.answer("Рецепт не найден (возможно, удален)")
            return

        # Формируем красивый текст
        full_text = (
            f"🍳 <b>{recipe['dish_name']}</b>\n\n"
            f"{recipe['recipe_text']}\n\n"
            f"🛒 <i>{recipe.get('ingredients', '')}</i>"
        )
        
        builder = InlineKeyboardBuilder()
        
        # Кнопка "Удалить"
        # Передаем ID для точного удаления
        builder.row(InlineKeyboardButton(
            text="🗑 Удалить", 
            callback_data=f"delete_fav_id_{fav_id}"
        ))
        
        # Кнопка "Назад к списку" (возвращает на 1 страницу)
        builder.row(InlineKeyboardButton(
            text="🔙 К списку", 
            callback_data="fav_page_1"
        ))
        
        await callback.message.edit_text(full_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка просмотра рецепта: {e}", exc_info=True)
        await callback.answer("Ошибка")


# --- 3. УДАЛЕНИЕ ПО ID (из режима просмотра) ---
async def handle_delete_favorite_by_id(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    
    try:
        # delete_fav_id_123
        fav_id = int(callback.data.split('_')[3])
        
        # Нам нужно имя блюда для сообщения, поэтому сначала достанем его (если еще не удалено)
        # Но для простоты просто удалим по ID.
        # В favorites_repo нужен метод remove_favorite_by_id, но можно и через SQL выполнить
        # Для простоты используем SQL напрямую или добавляем метод в repo.
        # ДАВАЙТЕ ЛУЧШЕ ПОЛУЧИМ РЕЦЕПТ, ЧТОБЫ УЗНАТЬ ИМЯ, А ПОТОМ УДАЛИМ
        
        fav = await favorites_repo.get_favorite_by_id(fav_id)
        if not fav:
            await callback.answer("Уже удалено")
            await handle_favorite_pagination(callback) # Возврат к списку
            return

        # Удаляем (используем имя, так как метод репо просит имя, 
        # но лучше добавить remove_by_id в репо. Сейчас используем имя для совместимости)
        success = await favorites_repo.remove_favorite(user_id, fav['dish_name'])
        
        if success:
            await callback.answer("🗑 Рецепт удален")
            # Возвращаемся к списку
            # Подменяем callback.data, чтобы функция пагинации показала 1 страницу
            callback.data = "fav_page_1" 
            await handle_favorite_pagination(callback)
        else:
            await callback.answer("Ошибка удаления")
            
    except Exception as e:
        logger.error(f"Ошибка удаления: {e}", exc_info=True)
        await callback.answer("Ошибка")


# --- 4. ДОБАВЛЕНИЕ (Осталось без изменений, кроме import track_safely) ---
async def handle_add_to_favorites(callback: CallbackQuery):
    # ... (Ваш код из предыдущего рабочего варианта для добавления) ...
    # Я скопирую его сюда для целостности файла
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
        
        # ВАЖНО: Тут мы пока используем заглушку, так как полный текст не в State.
        # В идеале нужно парсить сообщение или сохранять текст при генерации.
        recipe_text = f"Рецепт: {dish_name}\n\n(Текст из кэша генерации)"
        products = state_manager.get_products(user_id) or ""
        
        favorite = FavoriteRecipe(
            user_id=user_id,
            dish_name=dish_name,
            recipe_text=recipe_text,
            ingredients=products,
            language=lang,
            category=Category(category_str) if category_str in Category.__members__ else None
        )
        
        if await favorites_repo.count_favorites(user_id) >= 100:
             await callback.answer(get_text(lang, "favorite_limit").format(limit=100))
             return

        success = await favorites_repo.add_favorite(favorite)
        
        if success:
            await callback.answer(get_text(lang, "favorite_added").format(dish_name=dish_name))
            await track_safely(user_id, "favorite_added", {"dish_name": dish_name})
            await update_favorite_button(callback, dish_index, True, lang)
        else:
            await callback.answer("⚠️ Ошибка при сохранении")
    except Exception as e:
        logger.error(f"Error adding fav: {e}", exc_info=True)
        await callback.answer("Ошибка")

# --- 5. УДАЛЕНИЕ ИЗ КАРТОЧКИ ГЕНЕРАЦИИ (Без изменений) ---
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
            await callback.answer("Ошибка")
    except Exception as e:
        logger.error(f"Error removing fav: {e}", exc_info=True)
        await callback.answer("Ошибка")

# Вспомогательная функция (без изменений)
async def update_favorite_button(callback: CallbackQuery, dish_index: int, is_favorite: bool, lang: str):
    try:
        keyboard = callback.message.reply_markup
        if not keyboard: return
        builder = InlineKeyboardBuilder()
        for row in keyboard.inline_keyboard:
            new_row = []
            for button in row:
                if button.callback_data and ("add_fav" in button.callback_data or "remove_fav" in button.callback_data):
                    if is_favorite:
                        new_btn = InlineKeyboardButton(text=get_text(lang, "btn_remove_from_fav"), callback_data=f"remove_fav_{dish_index}")
                    else:
                        new_btn = InlineKeyboardButton(text=get_text(lang, "btn_add_to_fav"), callback_data=f"add_fav_{dish_index}")
                    new_row.append(new_btn)
                else:
                    new_row.append(button)
            builder.row(*new_row)
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    except Exception as e:
        logger.error(f"Btn update error: {e}")


# --- РЕГИСТРАЦИЯ ---
def register_favorites_handlers(dp: Dispatcher):
    # 1. Список (пагинация)
    dp.callback_query.register(handle_favorite_pagination, F.data.startswith("fav_page_"))
    
    # 2. Просмотр конкретного рецепта (НОВОЕ)
    dp.callback_query.register(handle_view_favorite, F.data.startswith("view_fav_"))
    
    # 3. Удаление конкретного рецепта по ID (НОВОЕ)
    dp.callback_query.register(handle_delete_favorite_by_id, F.data.startswith("delete_fav_id_"))
    
    # 4. Добавление/Удаление при генерации
    dp.callback_query.register(handle_add_to_favorites, F.data.startswith("add_fav_"))
    dp.callback_query.register(handle_remove_from_favorites, F.data.startswith("remove_fav_"))
