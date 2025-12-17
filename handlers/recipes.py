import logging
from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from services.groq_service import groq_service
from locales.texts import get_text
from state_manager import state_manager

logger = logging.getLogger(__name__)

# --- Вспомогательная функция для безопасного логирования метрик ---
# Эта функция должна быть в каждом файле хендлеров, пока она не вынесена в отдельный util-модуль
async def track_safely(user_id: int, event_name: str, data: dict = None):
    """Оборачивает логирование метрик в try/except"""
    try:
        await metrics.track_event(user_id, event_name, data)
    except Exception as e:
        logger.error(f"❌ Ошибка записи метрики ({event_name}): {e}", exc_info=True)


async def handle_text_message(message: Message):
    """Обрабатывает текстовые сообщения с продуктами"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Получаем язык для сообщений
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Проверяем лимиты
    allowed, used, limit = await users_repo.check_and_increment_request(user_id, "text")
    
    if not allowed:
        # ИСПРАВЛЕНО: Используем КОРРЕКТНЫЙ ключ limit_text_exceeded
        await message.answer(
            get_text(lang, "limit_text_exceeded", used=used, limit=limit),
            parse_mode="HTML"
        )
        return

    # Сохраняем продукты в состоянии
    state_manager.set_products(user_id, text)
    
    # Отправляем сообщение о процессе
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    try:
        # Анализируем категории
        categories = await groq_service.analyze_products(text, lang)
        
        await wait_msg.delete()
        
        if not categories:
            # ИСПРАВЛЕНИЕ: Используем error_not_enough_products при пустом ответе Groq
            await track_safely(user_id, "category_analysis_failed", {"language": lang, "products": text})
            await message.answer(get_text(lang, "error_not_enough_products"))
            return
        
        # Сохраняем категории в состоянии
        state_manager.set_categories(user_id, categories)
        
        # Создаём клавиатуру с категориями
        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, category),
                    callback_data=f"cat_{category}"
                )
            )
        
        # Кнопка сброса
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_restart"),
                callback_data="restart"
            )
        )
        
        await message.answer(
            get_text(lang, "choose_category"),
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        # Логируем полный Traceback ошибки
        logger.error(f"❌ Ошибка анализа категорий (handle_text_message): {e}", exc_info=True)
        await wait_msg.delete()
        await message.answer(get_text(lang, "error_generation"))


async def handle_category_selection(callback: CallbackQuery):
    """Обрабатывает выбор категории"""
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    
    category = callback.data.split('_')[1]
    products = state_manager.get_products(user_id)
    
    if not products:
        await callback.message.edit_text(get_text(lang, "start_manual"))
        await callback.answer()
        return

    # Отправляем сообщение о процессе
    wait_msg = await callback.message.edit_text(get_text(lang, "processing"))
    await callback.answer()

    try:
        # Генерируем список блюд (KeyError: '"name"' решен в GroqService)
        dishes = await groq_service.generate_dishes_list(products, category, lang)
        
        await wait_msg.delete()
        
        if not dishes:
            await track_safely(user_id, "dish_list_failed", {"language": lang, "category": category, "products": products})
            await callback.message.answer(get_text(lang, "error_generation"))
            return
        
        # Сохраняем блюда в состоянии
        state_manager.set_generated_dishes(user_id, dishes)
        
        # Создаём клавиатуру с блюдами
        builder = InlineKeyboardBuilder()
        for i, dish in enumerate(dishes):
            builder.row(
                InlineKeyboardButton(
                    text=f"{dish.get('name')}",
                    callback_data=f"dish_{i}"
                )
            )
        
        # Кнопка сброса
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_back"),
                callback_data="back_to_categories"
            )
        )
        
        await callback.message.answer(
            get_text(lang, "choose_dish").format(category=get_text(lang, category)),
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации списка блюд (handle_category_selection): {e}", exc_info=True)
        await wait_msg.delete()
        await callback.message.answer(get_text(lang, "error_generation"))


async def handle_dish_selection(callback: CallbackQuery):
    """Обрабатывает выбор конкретного блюда и генерирует рецепт"""
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    
    try:
        dish_index = int(callback.data.split('_')[1])
        dishes = state_manager.get_generated_dishes(user_id)
        
        if not dishes or dish_index >= len(dishes):
            await callback.message.edit_text(get_text(lang, "error_session_expired"))
            await callback.answer()
            return

        dish = dishes[dish_index]
        products = state_manager.get_products(user_id)
        
        # Сохраняем текущее блюдо
        state_manager.set_current_dish(user_id, dish)

        # Отправляем сообщение о процессе
        wait_msg = await callback.message.edit_text(get_text(lang, "processing"))
        await callback.answer()
        
        # Генерируем рецепт
        recipe = await groq_service.generate_recipe(dish.get('name'), products, lang)
        
        await wait_msg.delete()

        # Проверка на safety
        if get_text(lang, "safety_refusal") in recipe:
             await callback.message.answer(get_text(lang, "safety_refusal"))
             return

        # Добавляем метрику (ЗАЩИЩЕНО)
        await track_safely(
            user_id,
            "recipe_generated",
            {
                "dish_name": dish.get('name'),
                "language": lang,
                "category": dish.get('category', 'unknown'),
                "product_count": len(products.split(','))
            }
        )
        
        # Проверяем избранное
        is_favorite = await favorites_repo.is_favorite(user_id, dish.get('name'))
        
        builder = InlineKeyboardBuilder()
        
        # Кнопка избранного
        if is_favorite:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_remove_from_fav"),
                    callback_data=f"remove_fav_{dish_index}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_add_to_fav"),
                    callback_data=f"add_fav_{dish_index}"
                )
            )
        
        # Кнопки навигации
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_another"),
                callback_data=callback.data  # Повторить тот же запрос
            ),
            InlineKeyboardButton(
                text=get_text(lang, "btn_back"),
                callback_data="back_to_categories"
            )
        )
        
        # Отправляем новый рецепт
        await callback.message.answer(recipe, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации рецепта (handle_dish_selection): {e}", exc_info=True)
        try:
            await wait_msg.delete() 
        except:
            pass
        await callback.message.answer(get_text(lang, "error_generation")) 
        await callback.answer(get_text(lang, "error_generation"))


async def handle_back_to_categories(callback: CallbackQuery):
    """Возвращает пользователя к выбору категорий"""
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'ru')
    
    categories = state_manager.get_categories(user_id)
    
    if not categories:
        await callback.message.edit_text(get_text(lang, "error_session_expired"))
        await callback.answer()
        return
        
    # Создаём клавиатуру с категориями
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, category),
                callback_data=f"cat_{category}"
            )
        )
    
    # Кнопка сброса
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_restart"),
            callback_data="restart"
        )
    )
    
    await callback.message.edit_text(
        get_text(lang, "choose_category"),
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

def register_recipe_handlers(dp: Dispatcher):
    """Регистрирует обработчики рецептов"""
    # Текстовые сообщения
    dp.message.register(handle_text_message, F.text)
    
    # Коллбэки
    dp.callback_query.register(handle_category_selection, F.data.startswith("cat_"))
    dp.callback_query.register(handle_dish_selection, F.data.startswith("dish_"))
    dp.callback_query.register(handle_back_to_categories, F.data == "back_to_categories")