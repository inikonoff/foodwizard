import logging
from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from services.groq_service import groq_service
from locales.texts import get_text
from state_manager import state_manager

logger = logging.getLogger(__name__)

async def handle_text_message(message: Message):
    """Обрабатывает текстовые сообщения с продуктами"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # ВАЖНО: Игнорируем команды (они начинаются с /)
    if text.startswith('/'):
        return
    
    # Проверяем лимиты
    allowed, used, limit = await users_repo.check_and_increment_request(user_id, "text")
    
    if not allowed:
        # Получаем язык для сообщения об ошибке
        user_data = await users_repo.get_user(user_id)
        lang = user_data.get('language_code', 'ru') if user_data else 'ru'
        
        await message.answer(
            f"❌ <b>Лимит исчерпан!</b>\n\n"
            f"Вы использовали {used} из {limit} текстовых запросов сегодня.\n"
            f"Лимиты обновляются каждый день в 00:00.\n\n"
            f"💎 <b>Хотите больше?</b> Используйте команду /stats",
            parse_mode="HTML"
        )
        return
    
    # Получаем язык пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Проверяем, является ли это прямым запросом рецепта
    direct_keywords = ["рецепт ", "recipe ", "рецепт для ", "recipe for ", "дай рецепт "]
    if any(text.lower().startswith(keyword) for keyword in direct_keywords):
        await handle_direct_recipe_request(message, text, lang)
        return
    
    # Проверяем пасхалки
    if text.lower() in ["спасибо", "thanks", "danke", "merci", "grazie", "gracias"]:
        await message.answer(get_text(lang, "thanks"))
        return
    
    # Проверяем длину сообщения
    if len(text) > 1000:
        await message.answer(get_text(lang, "error_too_long"))
        return
    
    # Получаем текущие продукты
    current_products = state_manager.get_products(user_id)
    
    # Если продуктов ещё нет, проверяем валидность
    if not current_products:
        is_valid = await groq_service.validate_ingredients(text, lang)
        if not is_valid:
            await message.answer(get_text(lang, "error_no_products"))
            return
        
        # Сохраняем продукты
        state_manager.set_products(user_id, text)
        await message.answer(get_text(lang, "products_accepted", products=text))
        
        # Анализируем категории
        await analyze_and_show_categories(message, user_id, text, lang)
    else:
        # Добавляем к существующим продуктам
        state_manager.append_products(user_id, text)
        all_products = state_manager.get_products(user_id)
        await message.answer(get_text(lang, "products_added", products=text))
        
        # Показываем категории с учётом новых продуктов
        await analyze_and_show_categories(message, user_id, all_products, lang)
    
    # Обновляем активность пользователя
    await users_repo.update_activity(user_id)

async def handle_direct_recipe_request(message: Message, text: str, lang: str):
    """Обрабатывает прямой запрос рецепта (например, "рецепт пиццы")"""
    user_id = message.from_user.id
    
    # Извлекаем название блюда
    keywords = ["рецепт", "recipe", "рецепт для", "recipe for", "дай рецепт"]
    dish_name = text.lower()
    for keyword in keywords:
        dish_name = dish_name.replace(keyword, "").strip()
    
    if not dish_name or len(dish_name) < 2:
        await message.answer(get_text(lang, "error_no_products"))
        return
    
    # Показываем сообщение о обработке
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    try:
        # Генерируем рецепт
        recipe = await groq_service.generate_freestyle_recipe(dish_name, lang)
        
        await wait_msg.delete()
        
        if not recipe or "❌" in recipe:
            await message.answer(get_text(lang, "error_generation"))
            return
        
        # Проверяем, есть ли уже в избранном
        is_favorite = await favorites_repo.is_favorite(user_id, dish_name)
        
        # Создаём клавиатуру с кнопками
        builder = InlineKeyboardBuilder()
        
        # Кнопка избранного
        if is_favorite:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_remove_from_fav"),
                    callback_data=f"remove_fav_direct_{dish_name.replace(' ', '_')}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_add_to_fav"),
                    callback_data=f"add_fav_direct_{dish_name.replace(' ', '_')}"
                )
            )
        
        # Кнопка другого варианта
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_another"),
                callback_data=f"repeat_recipe_{dish_name.replace(' ', '_')}"
            )
        )
        
        # Отправляем рецепт
        await message.answer(recipe, reply_markup=builder.as_markup(), parse_mode="Markdown")
        
        # Логируем генерацию рецепта
        await metrics.track_event(
            user_id=user_id,
            event_name="recipe_generated",
            metadata={
                "dish_name": dish_name,
                "lang": lang,
                "category": "direct"
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка генерации рецепта: {e}")
        await wait_msg.delete()
        await message.answer(get_text(lang, "error_generation"))

async def analyze_and_show_categories(message: Message, user_id: int, products: str, lang: str):
    """Анализирует продукты и показывает категории"""
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    try:
        logger.info(f"Анализ продуктов для пользователя {user_id}: {products}")
        
        # Анализируем категории
        categories = await groq_service.analyze_products(products, lang)
        
        logger.info(f"Получены категории для пользователя {user_id}: {categories}")
        
        await wait_msg.delete()
        
        if not categories:
            logger.error(f"Пустой список категорий для пользователя {user_id}")
            await message.answer(get_text(lang, "error_generation"))
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
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа категорий: {e}", exc_info=True)
        try:
            await wait_msg.delete()
        except:
            pass
        await message.answer(get_text(lang, "error_generation"))

async def handle_category_selection(callback: CallbackQuery):
    """Обрабатывает выбор категории"""
    user_id = callback.from_user.id
    category = callback.data.split('_')[1]  # cat_soup -> soup
    
    logger.info(f"Пользователь {user_id} выбрал категорию: {category}")
    
    # Получаем язык пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Получаем продукты
    products = state_manager.get_products(user_id)
    
    if not products:
        logger.error(f"Нет продуктов для пользователя {user_id}")
        await callback.answer("Сначала отправьте продукты")
        return
    
    logger.info(f"Продукты для пользователя {user_id}: {products}")
    
    wait_msg = await callback.message.answer(get_text(lang, "processing"))
    
    try:
        logger.info(f"Генерация списка блюд для категории: {category}")
        
        # Генерируем список блюд
        dishes = await groq_service.generate_dish_list(products, category, lang)
        
        logger.info(f"Сгенерировано {len(dishes)} блюд")
        
        await wait_msg.delete()
        
        if not dishes:
            logger.error(f"Пустой список блюд для категории {category}")
            await callback.message.answer(get_text(lang, "error_generation"))
            await callback.answer()
            return
        
        # Сохраняем блюда в состоянии
        state_manager.set_generated_dishes(user_id, dishes)
        
        # Создаём клавиатуру с блюдами
        builder = InlineKeyboardBuilder()
        
        for i, dish in enumerate(dishes):
            dish_name = dish.get('name', f'Блюдо {i+1}')
            # Обрезаем длинные названия
            if len(dish_name) > 35:
                dish_name = dish_name[:32] + "..."
            
            builder.row(
                InlineKeyboardButton(
                    text=dish_name,
                    callback_data=f"dish_{i}"
                )
            )
        
        # Кнопки навигации
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_back"),
                callback_data="back_to_categories"
            ),
            InlineKeyboardButton(
                text=get_text(lang, "btn_restart"),
                callback_data="restart"
            )
        )
        
        await callback.message.edit_text(
            get_text(lang, "choose_dish"),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка генерации списка блюд: {e}", exc_info=True)
        try:
            await wait_msg.delete()
        except:
            pass
        await callback.answer("❌ Ошибка генерации")

async def handle_dish_selection(callback: CallbackQuery):
    """Обрабатывает выбор блюда"""
    user_id = callback.from_user.id
    dish_index = int(callback.data.split('_')[1])  # dish_0 -> 0
    
    logger.info(f"Пользователь {user_id} выбрал блюдо с индексом: {dish_index}")
    
    # Получаем язык пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Получаем блюдо
    dishes = state_manager.get_generated_dishes(user_id)
    if not dishes or dish_index >= len(dishes):
        logger.error(f"Блюдо с индексом {dish_index} не найдено для пользователя {user_id}")
        await callback.answer("Блюдо не найдено")
        return
    
    dish = dishes[dish_index]
    dish_name = dish.get('name')
    
    logger.info(f"Выбрано блюдо: {dish_name}")
    
    # Получаем продукты
    products = state_manager.get_products(user_id) or ""
    
    wait_msg = await callback.message.answer(get_text(lang, "processing"))
    
    try:
        # Генерируем рецепт
        recipe = await groq_service.generate_recipe(dish_name, products, lang)
        
        await wait_msg.delete()
        
        if not recipe or "❌" in recipe:
            await callback.message.answer(get_text(lang, "error_generation"))
            await callback.answer()
            return
        
        # Сохраняем текущее блюдо
        state_manager.set_current_dish(user_id, dish_name)
        
        # Проверяем, есть ли уже в избранном
        is_favorite = await favorites_repo.is_favorite(user_id, dish_name)
        
        # Создаём клавиатуру
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
                callback_data=f"repeat_dish_{dish_index}"
            ),
            InlineKeyboardButton(
                text=get_text(lang, "btn_to_categories"),
                callback_data="back_to_categories"
            )
        )
        
        await callback.message.answer(recipe, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await callback.answer()
        
        # Логируем генерацию рецепта
        await metrics.track_event(
            user_id=user_id,
            event_name="recipe_generated",
            metadata={
                "dish_name": dish_name,
                "lang": lang,
                "category": state_manager.get_categories(user_id)[0] if state_manager.get_categories(user_id) else "unknown"
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка генерации рецепта: {e}", exc_info=True)
        try:
            await wait_msg.delete()
        except:
            pass
        await callback.answer("❌ Ошибка")

async def handle_back_to_categories(callback: CallbackQuery):
    """Возвращает к выбору категорий"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} возвращается к категориям")
    
    # Получаем язык пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Получаем категории
    categories = state_manager.get_categories(user_id)
    
    if not categories:
        logger.error(f"Нет сохранённых категорий для пользователя {user_id}")
        await callback.answer("Нет сохранённых категорий")
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

async def handle_restart(callback: CallbackQuery):
    """Сбрасывает сессию"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} перезапускает сессию")
    
    # Получаем язык пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Очищаем сессию
    state_manager.clear_session(user_id)
    
    await callback.message.edit_text(
        get_text(lang, "start_manual"),
        parse_mode="Markdown"
    )
    await callback.answer()

async def handle_repeat_recipe(callback: CallbackQuery):
    """Генерирует другой вариант рецепта"""
    user_id = callback.from_user.id
    
    # Проверяем лимиты
    allowed, used, limit = await users_repo.check_and_increment_request(user_id, "text")
    
    if not allowed:
        # Получаем язык для сообщения об ошибке
        user_data = await users_repo.get_user(user_id)
        lang = user_data.get('language_code', 'ru') if user_data else 'ru'
        
        await callback.answer(
            f"❌ Лимит исчерпан! {used}/{limit}",
            show_alert=True
        )
        return
    
    # Получаем язык пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Извлекаем название блюда или индекс
    data_parts = callback.data.split('_')
    
    if len(data_parts) >= 3 and data_parts[1] == "recipe":
        # Прямой рецепт (repeat_recipe_pizza)
        dish_name = '_'.join(data_parts[2:])
        products = ""
    elif len(data_parts) >= 3 and data_parts[1] == "dish":
        # Рецепт из списка (repeat_dish_0)
        dish_index = int(data_parts[2])
        dishes = state_manager.get_generated_dishes(user_id)
        if not dishes or dish_index >= len(dishes):
            await callback.answer("Блюдо не найдено")
            return
        dish_name = dishes[dish_index].get('name')
        products = state_manager.get_products(user_id) or ""
    else:
        # Текущее блюдо
        dish_name = state_manager.get_current_dish(user_id)
        products = state_manager.get_products(user_id) or ""
    
    if not dish_name:
        await callback.answer("Блюдо не выбрано")
        return
    
    wait_msg = await callback.message.answer(get_text(lang, "processing"))
    
    try:
        if products:
            recipe = await groq_service.generate_recipe(dish_name, products, lang)
        else:
            recipe = await groq_service.generate_freestyle_recipe(dish_name, lang)
        
        await wait_msg.delete()
        
        if not recipe or "❌" in recipe:
            await callback.message.answer(get_text(lang, "error_generation"))
            await callback.answer()
            return
        
        # Проверяем, есть ли уже в избранном
        is_favorite = await favorites_repo.is_favorite(user_id, dish_name)
        
        # Создаём клавиатуру
        builder = InlineKeyboardBuilder()
        
        # Кнопка избранного
        if is_favorite:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_remove_from_fav"),
                    callback_data=f"remove_fav_{dish_name.replace(' ', '_')}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=get_text(lang, "btn_add_to_fav"),
                    callback_data=f"add_fav_{dish_name.replace(' ', '_')}"
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
        logger.error(f"Ошибка повторной генерации рецепта: {e}", exc_info=True)
        try:
            await wait_msg.delete()
        except:
            pass
        await callback.answer("❌ Ошибка")

def register_recipe_handlers(dp: Dispatcher):
    """Регистрирует обработчики рецептов"""
    # Текстовые сообщения (НЕ команды!)
    dp.message.register(
        handle_text_message, 
        F.text,
        ~Command()  # Исключаем ВСЕ команды
    )
    
    # Коллбэки
    dp.callback_query.register(handle_category_selection, F.data.startswith("cat_"))
    dp.callback_query.register(handle_dish_selection, F.data.startswith("dish_"))
    dp.callback_query.register(handle_back_to_categories, F.data == "back_to_categories")
    dp.callback_query.register(handle_restart, F.data == "restart")
    dp.callback_query.register(handle_repeat_recipe, F.data.startswith(("repeat_recipe_", "repeat_dish_")))
   