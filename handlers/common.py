import logging
from datetime import datetime, timedelta
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db # Оставлен только из-за /admin reset
from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
from config import SUPPORTED_LANGUAGES, ADMIN_IDS, SECRET_PROMO_CODE

logger = logging.getLogger(__name__)

# --- Вспомогательная функция для безопасного логирования метрик ---
# Добавлен сюда, чтобы быть независимым от recipes.py
async def track_safely(user_id: int, event_name: str, data: dict = None):
    try:
        await metrics.track_event(user_id, event_name, data)
    except Exception as e:
        logger.error(f"❌ Ошибка записи метрики ({event_name}): {e}", exc_info=True)


# --- КОМАНДА /START ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    # Получаем или создаём пользователя
    user_data = await users_repo.get_or_create(
        user_id=user_id,
        first_name=first_name,
        username=username
    )
    
    # Определяем язык пользователя
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Отправляем приветственное сообщение
    welcome_text = get_text(lang, "welcome", name=first_name)
    start_manual = get_text(lang, "start_manual")
    
    # Создаём клавиатуру с основными командами
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_favorites"),
            callback_data="show_favorites"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_change_lang"),
            callback_data="change_language"
        ),
        InlineKeyboardButton(
            text=get_text(lang, "btn_help"),
            callback_data="show_help"
        )
    )
    
    full_text = f"{welcome_text}\n\n{start_manual}"
    await message.answer(full_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    # Логируем событие (ЗАЩИЩЕНО)
    await track_safely(user_id, "start_command", {"language": lang})

# --- КОМАНДА /FAVORITES ---
async def cmd_favorites(message: Message):
    user_id = message.from_user.id
    
    # Получаем данные пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Получаем первую страницу избранного
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page=1)
    
    if not favorites:
        await message.answer(get_text(lang, "favorites_empty"))
        return
    
    # Форматируем список рецептов
    recipes_text = ""
    for i, fav in enumerate(favorites, 1):
        date_str = fav['created_at'].strftime("%d.%m.%Y")
        recipes_text += get_text(lang, "favorites_recipe_item", 
                               num=i, dish=fav['dish_name'], date=date_str)
    
    # Создаём клавиатуру с пагинацией
    builder = InlineKeyboardBuilder()
    
    # Кнопки пагинации (опущен для краткости)
    if total_pages > 1:
        builder.row(
            InlineKeyboardButton(text=get_text(lang, "btn_prev"), callback_data=f"fav_page_1"),
            InlineKeyboardButton(text=f"1/{total_pages}", callback_data="noop"),
            InlineKeyboardButton(text=get_text(lang, "btn_next"), callback_data=f"fav_page_2")
        )
    
    # Кнопка возврата
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    # Отправляем сообщение
    text = get_text(lang, "favorites_list", page=1, total_pages=total_pages, recipes=recipes_text)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    # Логируем событие (ЗАЩИЩЕНО)
    await track_safely(user_id, "favorites_viewed", {"page": 1, "total": len(favorites)})

# --- КОМАНДА /LANG --- (без изменений)
async def cmd_lang(message: Message):
    user_id = message.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    current_lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    builder = InlineKeyboardBuilder()
    for lang_code in SUPPORTED_LANGUAGES:
        builder.row(
            InlineKeyboardButton(
                text=get_text(current_lang, f"lang_{lang_code}"),
                callback_data=f"set_lang_{lang_code}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text=get_text(current_lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    await message.answer(
        get_text(current_lang, "choose_language"),
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# --- КОМАНДА /HELP ---
async def cmd_help(message: Message):
    user_id = message.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    help_text = f"{get_text(lang, 'help_title')}\n{get_text(lang, 'help_text')}"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    await message.answer(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    # Логируем событие (ЗАЩИЩЕНО)
    await track_safely(user_id, "help_viewed", {"language": lang})

# --- КОМАНДА /CODE ---
async def cmd_code(message: Message):
    user_id = message.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "Введите код. Пример:\n"
            f"<code>/code {SECRET_PROMO_CODE}</code>",
            parse_mode="HTML"
        )
        return
    
    code = args[1].strip()
    
    if code == SECRET_PROMO_CODE:
        success = await users_repo.activate_premium(user_id, days=365*99)
        
        if success:
            response = (
                "?? <b>Код принят!</b>\n\n"
                "Активирован временный доступ к премиум функциям на <b>99 лет</b>.\n"
                "По истечении срока действия не забудьте продлить подписку. ??"
            )
            await message.answer(response, parse_mode="HTML")
            
            # Логируем активацию премиума (ЗАЩИЩЕНО)
            await track_safely(user_id, "premium_activated", {
                "method": "promo_code",
                "days": 365*99
            })
        else:
            await message.answer("? Ошибка активации премиума")
    else:
        await message.answer("? Неверный код.")

# --- КОМАНДА /STATS --- (без изменений)
async def cmd_stats(message: Message):
    user_id = message.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    usage_stats = await users_repo.get_usage_stats(user_id)
    
    if not usage_stats:
        await message.answer("Статистика недоступна")
        return
    
    # ... (код формирования сообщения) ...
    status = "?? ПРЕМИУМ" if usage_stats['is_premium'] else "?? БЕСПЛАТНО"
    
    if usage_stats['premium_until']:
        premium_until = usage_stats['premium_until'].strftime("%d.%m.%Y")
        status += f" (до {premium_until})"
    
    stats_text = (
        f"?? <b>Ваша статистика</b>\n\n"
        f"{status}\n\n"
        f"?? <b>Текстовые запросы:</b>\n"
        f"   Использовано: {usage_stats['text_requests_used']}/{usage_stats['text_requests_limit']}\n"
        f"   Осталось: {usage_stats['remaining_text']}\n\n"
        f"?? <b>Голосовые запросы:</b>\n"
        f"   Использовано: {usage_stats['voice_requests_used']}/{usage_stats['voice_requests_limit']}\n"
        f"   Осталось: {usage_stats['remaining_voice']}\n\n"
        f"?? <b>Всего запросов:</b> {usage_stats['total_requests']}\n"
        f"?? <b>Сброс лимитов:</b> {usage_stats['last_reset_date'].strftime('%d.%m.%Y')}"
    )
    
    builder = InlineKeyboardBuilder()
    
    if not usage_stats['is_premium']:
        builder.row(InlineKeyboardButton(text="?? Купить премиум", callback_data="buy_premium"))
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await message.answer(stats_text, reply_markup=builder.as_markup(), parse_mode="HTML")

# --- КОМАНДА /ADMIN --- (без изменений)
async def cmd_admin(message: Message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await message.answer("? Доступ запрещён")
        return
    
    args = message.text.split()
    
    if len(args) < 2:
        # ... (ответ) ...
        help_text = (
            "?? <b>Админ-панель</b>\n\n"
            "<b>Команды:</b>\n"
            "/admin stats - общая статистика\n"
            "/admin premium [user_id] - выдать премиум\n"
            "/admin users [N] - список пользователей\n"
            "/admin reset [user_id] - сбросить лимиты\n"
            "/admin broadcast - рассылка\n"
        )
        await message.answer(help_text, parse_mode="HTML")
        return
    
    command = args[1].lower()
    
    if command == "stats":
        total_users = await users_repo.count_users()
        expired = await users_repo.check_premium_expiry()
        
        stats = (
            f"?? <b>Общая статистика</b>\n\n"
            f"?? Всего пользователей: {total_users}\n"
            f"?? Деактивировано премиумов: {expired}\n"
        )
        await message.answer(stats, parse_mode="HTML")
    
    elif command == "premium" and len(args) >= 3:
        try:
            target_user_id = int(args[2])
            days = int(args[3]) if len(args) >= 4 else 30
            
            success = await users_repo.activate_premium(target_user_id, days)
            
            if success:
                await message.answer(f"? Премиум выдан пользователю {target_user_id} на {days} дней")
            else:
                await message.answer(f"? Ошибка выдачи премиума")
        except ValueError:
            await message.answer("? Неверный формат ID пользователя")
    
    elif command == "users":
        limit = int(args[2]) if len(args) >= 3 else 10
        
        users = await users_repo.get_all_users(limit)
        
        if not users:
            await message.answer("Нет пользователей")
            return
        
        users_text = "?? <b>Последние пользователи:</b>\n\n"
        for i, user in enumerate(users, 1):
            premium = "??" if user['is_premium'] else "??"
            users_text += f"{i}. {user['first_name']} ({user['user_id']}) {premium}\n"
        
        await message.answer(users_text, parse_mode="HTML")
    
    elif command == "reset" and len(args) >= 3:
        try:
            target_user_id = int(args[2])
            
            async with db.connection() as conn:
                await conn.execute(
                    """
                    UPDATE users 
                    SET requests_today = 0, 
                        voice_requests_today = 0,
                        last_reset_date = CURRENT_DATE
                    WHERE user_id = $1
                    """,
                    target_user_id
                )
            
            await message.answer(f"? Лимиты пользователя {target_user_id} сброшены")
        except ValueError:
            await message.answer("? Неверный формат ID пользователя")
    
    elif command == "broadcast":
        if len(args) < 3:
            await message.answer("Использование: /admin broadcast [сообщение]")
            return
        
        broadcast_text = " ".join(args[2:])
        users = await users_repo.get_all_users(1000)
        
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
                await message.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"?? <b>Объявление от администратора:</b>\n\n{broadcast_text}",
                    parse_mode="HTML"
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки рассылки пользователю {user['user_id']}: {e}", exc_info=True)
                fail_count += 1
        
        await message.answer(
            f"? Рассылка завершена:\n"
            f"? Успешно: {success_count}\n"
            f"? Ошибок: {fail_count}"
        )

# --- КОЛЛБЭКИ ---
# handle_change_language (без изменений)
async def handle_change_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    current_lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    builder = InlineKeyboardBuilder()
    for lang_code in SUPPORTED_LANGUAGES:
        builder.row(
            InlineKeyboardButton(
                text=get_text(current_lang, f"lang_{lang_code}"),
                callback_data=f"set_lang_{lang_code}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text=get_text(current_lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    await callback.message.edit_text(
        get_text(current_lang, "choose_language"),
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# handle_set_language (без изменений)
async def handle_set_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    lang_code = callback.data.split("_")[2]
    
    await users_repo.update_language(user_id, lang_code)
    
    user_data = await users_repo.get_user(user_id)
    final_lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    final_lang = final_lang if final_lang in SUPPORTED_LANGUAGES else 'ru'

    first_name = user_data.get('first_name', 'User') if user_data else 'User'
    
    welcome_text = get_text(final_lang, "welcome", name=first_name)
    start_manual = get_text(final_lang, "start_manual")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(final_lang, "btn_favorites"), callback_data="show_favorites"))
    builder.row(InlineKeyboardButton(text=get_text(final_lang, "btn_change_lang"), callback_data="change_language"),
                InlineKeyboardButton(text=get_text(final_lang, "btn_help"), callback_data="show_help"))
    
    full_text = f"{welcome_text}\n\n{start_manual}"
    await callback.message.edit_text(
        full_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    
    await track_safely(user_id, "language_changed", {"language": lang_code})
    await callback.answer(get_text(final_lang, "lang_changed"))

# handle_show_favorites (без изменений)
async def handle_show_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page=1)
    
    if not favorites:
        await callback.message.edit_text(get_text(lang, "favorites_empty"))
        await callback.answer()
        return
    
    recipes_text = ""
    for i, fav in enumerate(favorites, 1):
        date_str = fav['created_at'].strftime("%d.%m.%Y")
        recipes_text += get_text(lang, "favorites_recipe_item", num=i, dish=fav['dish_name'], date=date_str)
    
    builder = InlineKeyboardBuilder()
    
    if total_pages > 1:
        builder.row(
            InlineKeyboardButton(text=get_text(lang, "btn_prev"), callback_data=f"fav_page_1"),
            InlineKeyboardButton(text=f"1/{total_pages}", callback_data="noop"),
            InlineKeyboardButton(text=get_text(lang, "btn_next"), callback_data=f"fav_page_2")
        )
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    text = get_text(lang, "favorites_list", page=1, total_pages=total_pages, recipes=recipes_text)
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

# handle_show_help (без изменений)
async def handle_show_help(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    help_text = f"{get_text(lang, 'help_title')}\n{get_text(lang, 'help_text')}"
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await callback.message.edit_text(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

# handle_main_menu (без изменений)
async def handle_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    first_name = user_data.get('first_name', 'User') if user_data else 'User'
    
    welcome_text = get_text(lang, "welcome", name=first_name)
    start_manual = get_text(lang, "start_manual")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_favorites"), callback_data="show_favorites"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_change_lang"), callback_data="change_language"),
                InlineKeyboardButton(text=get_text(lang, "btn_help"), callback_data="show_help"))
    
    full_text = f"{welcome_text}\n\n{start_manual}"
    await callback.message.edit_text(
        full_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# handle_noop, handle_buy_premium, handle_premium_1_month, handle_premium_3_months, handle_premium_1_year (без изменений)
async def handle_noop(callback: CallbackQuery):
    await callback.answer()

async def handle_buy_premium(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="1 месяц - 100 звёзд ?", callback_data="premium_1_month"))
    builder.row(InlineKeyboardButton(text="3 месяца - 250 звёзд ? (экономия 17%)", callback_data="premium_3_months"))
    builder.row(InlineKeyboardButton(text="1 год - 800 звёзд ? (экономия 33%)", callback_data="premium_1_year"))
    builder.row(InlineKeyboardButton(text="?? Вернуться", callback_data="main_menu"))
    
    text = (
        "?? <b>Премиум подписка</b>\n\n"
        "? <b>Что входит:</b>\n"
        "  100 текстовых запросов в день\n"
        "  50 голосовых запросов в день\n"
        "  Приоритетная обработка\n"
        "  Доступ к новым функциям первым\n"
        "  Поддержка разработчика ??\n\n"
        "?? <b>Лимиты обновляются каждый день в 00:00</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

async def handle_premium_1_month(callback: CallbackQuery):
    await callback.answer("?? Эта функция скоро будет доступна!")

async def handle_premium_3_months(callback: CallbackQuery):
    await callback.answer("?? Эта функция скоро будет доступна!")

async def handle_premium_1_year(callback: CallbackQuery):
    await callback.answer("?? Эта функция скоро будет доступна!")


# 