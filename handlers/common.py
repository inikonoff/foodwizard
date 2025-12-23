import logging
from datetime import datetime, timedelta
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db 
from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
from config import SUPPORTED_LANGUAGES, ADMIN_IDS, SECRET_PROMO_CODE

logger = logging.getLogger(__name__)

# --- Вспомогательная функция для безопасного логирования метрик ---
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
    
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    welcome_text = get_text(lang, "welcome", name=first_name)
    start_manual = get_text(lang, "start_manual")
    
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
    
    await track_safely(user_id, "start_command", {"language": lang})

# --- КОМАНДА /FAVORITES (С кнопками) ---
async def cmd_favorites(message: Message):
    user_id = message.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Получаем 1-ю страницу
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page=1)
    
    if not favorites:
        await message.answer(get_text(lang, "favorites_empty"))
        return
    
    # Текст заголовка
    header_text = get_text(lang, "favorites_title") + f" (стр. 1/{total_pages})"
    
    builder = InlineKeyboardBuilder()
    
    # === ГЕНЕРАЦИЯ КНОПОК РЕЦЕПТОВ ===
    for fav in favorites:
        date_str = fav['created_at'].strftime("%d.%m")
        btn_text = f"{fav['dish_name']} ({date_str})"
        
        builder.row(InlineKeyboardButton(
            text=btn_text, 
            callback_data=f"view_fav_{fav['id']}"
        ))
    
    # === ПАГИНАЦИЯ ===
    if total_pages > 1:
        pagination_row = []
        pagination_row.append(InlineKeyboardButton(text=f"1/{total_pages}", callback_data="noop"))
        pagination_row.append(InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
        builder.row(*pagination_row)
    
    # Кнопка возврата
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu")
    )
    
    await message.answer(header_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    await track_safely(user_id, "favorites_viewed", {"page": 1, "total": len(favorites)})

# --- КОМАНДА /LANG --- 
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
        InlineKeyboardButton(text=get_text(current_lang, "btn_back"), callback_data="main_menu")
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
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await message.answer(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    await track_safely(user_id, "help_viewed", {"language": lang})

# --- КОМАНДА /CODE (БЕЗОПАСНАЯ) ---
async def cmd_code(message: Message):
    user_id = message.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "Введите код. Пример:\n"
            "<code>/code PROMO123</code>", # Заглушка вместо реального кода
            parse_mode="HTML"
        )
        return
    
    code = args[1].strip()
    
    if code == SECRET_PROMO_CODE:
        success = await users_repo.activate_premium(user_id, days=365*99)
        
        if success:
            response = (
                "💎 <b>Код принят!</b>\n\n"
                "Активирован временный доступ к премиум функциям на <b>99 лет</b>.\n"
                "По истечении срока действия не забудьте продлить подписку. 😉"
            )
            await message.answer(response, parse_mode="HTML")
            
            await track_safely(user_id, "premium_activated", {
                "method": "promo_code",
                "days": 365*99
            })
        else:
            await message.answer("⚠️ Ошибка активации премиума")
    else:
        await message.answer("🚫 Неверный код.")

# --- КОМАНДА /STATS ---
async def cmd_stats(message: Message):
    user_id = message.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    usage_stats = await users_repo.get_usage_stats(user_id)
    
    if not usage_stats:
        await message.answer("Статистика недоступна")
        return
    
    status = "💎 ПРЕМИУМ" if usage_stats['is_premium'] else "👤 БЕСПЛАТНО"
    
    if usage_stats['premium_until']:
        premium_until = usage_stats['premium_until'].strftime("%d.%m.%Y")
        status += f" (до {premium_until})"
    
    stats_text = (
        f"📊 <b>Ваша статистика</b>\n\n"
        f"{status}\n\n"
        f"📝 <b>Текстовые запросы:</b>\n"
        f"   Использовано: {usage_stats['text_requests_used']}/{usage_stats['text_requests_limit']}\n"
        f"   Осталось: {usage_stats['remaining_text']}\n\n"
        f"🎤 <b>Голосовые запросы:</b>\n"
        f"   Использовано: {usage_stats['voice_requests_used']}/{usage_stats['voice_requests_limit']}\n"
        f"   Осталось: {usage_stats['remaining_voice']}\n\n"
        f"📈 <b>Всего запросов:</b> {usage_stats['total_requests']}\n"
        f"🔄 <b>Сброс лимитов:</b> {usage_stats['last_reset_date'].strftime('%d.%m.%Y')}"
    )
    
    builder = InlineKeyboardBuilder()
    
    if not usage_stats['is_premium']:
        builder.row(InlineKeyboardButton(text="💎 Купить премиум", callback_data="buy_premium"))
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await message.answer(stats_text, reply_markup=builder.as_markup(), parse_mode="HTML")

# --- КОМАНДА /ADMIN ---
async def cmd_admin(message: Message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await message.answer("🚫 Доступ запрещён")
        return
    
    args = message.text.split()
    
    if len(args) < 2:
        help_text = (
            "👑 <b>Админ-панель</b>\n\n"
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
            f"📊 <b>Общая статистика</b>\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"🚫 Деактивировано премиумов: {expired}\n"
        )
        await message.answer(stats, parse_mode="HTML")
    
    elif command == "premium" and len(args) >= 3:
        try:
            target_user_id = int(args[2])
            days = int(args[3]) if len(args) >= 4 else 30
            
            success = await users_repo.activate_premium(target_user_id, days)
            
            if success:
                await message.answer(f"✅ Премиум выдан пользователю {target_user_id} на {days} дней")
            else:
                await message.answer(f"⚠️ Ошибка выдачи премиума")
        except ValueError:
            await message.answer("⚠️ Неверный формат ID пользователя")
    
    elif command == "users":
        limit = int(args[2]) if len(args) >= 3 else 10
        
        users = await users_repo.get_all_users(limit)
        
        if not users:
            await message.answer("Нет пользователей")
            return
        
        users_text = "👥 <b>Последние пользователи:</b>\n\n"
        for i, user in enumerate(users, 1):
            premium = "💎" if user['is_premium'] else "👤"
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
            
            await message.answer(f"✅ Лимиты пользователя {target_user_id} сброшены")
        except ValueError:
            await message.answer("⚠️ Неверный формат ID пользователя")
    
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
                    text=f"📢 <b>Объявление от администратора:</b>\n\n{broadcast_text}",
                    parse_mode="HTML"
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки рассылки пользователю {user['user_id']}: {e}", exc_info=True)
                fail_count += 1
        
        await message.answer(
            f"✅ Рассылка завершена:\n"
            f"📨 Успешно: {success_count}\n"
            f"❌ Ошибок: {fail_count}"
        )

# --- КОЛЛБЭКИ ИНТЕРФЕЙСА ---
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
        InlineKeyboardButton(text=get_text(current_lang, "btn_back"), callback_data="main_menu")
    )
    
    await callback.message.edit_text(
        get_text(current_lang, "choose_language"),
        reply_markup=builder.as_markup()
    )
    await callback.answer()

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
    
    # ИСПРАВЛЕНО: full_text -> text
    await callback.message.edit_text(
        text=f"{welcome_text}\n\n{start_manual}", 
        reply_markup=builder.as_markup(), 
        parse_mode="Markdown"
    )
    
    await track_safely(user_id, "language_changed", {"language": lang_code})
    await callback.answer(get_text(final_lang, "lang_changed"))

async def handle_show_favorites(callback: CallbackQuery):
    # Эта функция для кнопки в меню. Она должна перенаправлять на ту же логику, что и cmd_favorites
    # Но так как callback требует редактирования, повторим логику с edit_text
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page=1)
    
    if not favorites:
        await callback.message.edit_text(get_text(lang, "favorites_empty"))
        await callback.answer()
        return
    
    header_text = get_text(lang, "favorites_title") + f" (стр. 1/{total_pages})"
    
    builder = InlineKeyboardBuilder()
    
    for fav in favorites:
        date_str = fav['created_at'].strftime("%d.%m")
        btn_text = f"{fav['dish_name']} ({date_str})"
        builder.row(InlineKeyboardButton(text=btn_text, callback_data=f"view_fav_{fav['id']}"))
    
    if total_pages > 1:
        pagination_row = []
        pagination_row.append(InlineKeyboardButton(text=f"1/{total_pages}", callback_data="noop"))
        pagination_row.append(InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
        builder.row(*pagination_row)
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await callback.message.edit_text(header_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()
    await track_safely(user_id, "favorites_viewed", {"page": 1})

async def handle_show_help(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    help_text = f"{get_text(lang, 'help_title')}\n{get_text(lang, 'help_text')}"
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await callback.message.edit_text(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

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
    
    # ИСПРАВЛЕНО: full_text -> text
    await callback.message.edit_text(
        text=f"{welcome_text}\n\n{start_manual}", 
        reply_markup=builder.as_markup(), 
        parse_mode="Markdown"
    )
    await callback.answer()

async def handle_noop(callback: CallbackQuery):
    await callback.answer()

async def handle_buy_premium(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="1 месяц - 100 звёзд ⭐️", callback_data="premium_1_month"))
    builder.row(InlineKeyboardButton(text="3 месяца - 250 звёзд ⭐️ (экономия 17%)", callback_data="premium_3_months"))
    builder.row(InlineKeyboardButton(text="1 год - 800 звёзд ⭐️ (экономия 33%)", callback_data="premium_1_year"))
    builder.row(InlineKeyboardButton(text="🔙 Вернуться", callback_data="main_menu"))
    
    text = (
        "💎 <b>Премиум подписка</b>\n\n"
        "🚀 <b>Что входит:</b>\n"
        "  100 текстовых запросов в день\n"
        "  50 голосовых запросов в день\n"
        "  Приоритетная обработка\n"
        "  Доступ к новым функциям первым\n"
        "  Поддержка разработчика ❤️\n\n"
        "🔄 <b>Лимиты обновляются каждый день в 00:00</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

# --- ОБРАБОТЧИКИ ОПЛАТЫ (TELEGRAM STARS) ---
async def handle_premium_1_month(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="Премиум подписка (1 месяц)",
        description="Доступ к расширенным функциям бота на 30 дней.",
        payload="premium_30_days",
        provider_token="",  
        currency="XTR",
        prices=[LabeledPrice(label="1 месяц", amount=100)],
    )
    await callback.answer()

async def handle_premium_3_months(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="Премиум подписка (3 месяца)",
        description="Доступ к расширенным функциям бота на 90 дней. Выгодно!",
        payload="premium_90_days",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="3 месяца", amount=250)],
    )
    await callback.answer()

async def handle_premium_1_year(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="Премиум подписка (1 год)",
        description="Максимальный доступ на 365 дней.",
        payload="premium_365_days",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="1 год", amount=800)],
    )
    await callback.answer()

# --- ОБРАБОТКА САМОГО ПЛАТЕЖА ---
async def on_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

async def on_successful_payment(message: Message):
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload
    user_id = message.from_user.id
    
    days = 0
    if payload == "premium_30_days": days = 30
    elif payload == "premium_90_days": days = 90
    elif payload == "premium_365_days": days = 365
        
    if days > 0:
        success = await users_repo.activate_premium(user_id, days)
        if success:
            await message.answer(f"🌟 <b>Оплата прошла успешно!</b>\n\nВам начислен Премиум доступ на <b>{days} дней</b>.\nСпасибо за поддержку! ❤️", parse_mode="HTML")
            await track_safely(user_id, "payment_success", {"amount": payment_info.total_amount, "currency": payment_info.currency, "days": days})
        else:
            logger.error(f"Деньги списаны, но БД не обновилась! User: {user_id}, Days: {days}")
            await message.answer("⚠️ Оплата прошла, но произошла ошибка активации. Пожалуйста, свяжитесь с поддержкой.")

# --- РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ---
def register_common_handlers(dp: Dispatcher):
    # Команды
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_favorites, Command("favorites"))
    dp.message.register(cmd_lang, Command("lang"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_code, Command("code"))
    dp.message.register(cmd_stats, Command("stats"))
    dp.message.register(cmd_admin, Command("admin"))
    
    # Коллбэки интерфейса
    dp.callback_query.register(handle_change_language, F.data == "change_language")
    dp.callback_query.register(handle_set_language, F.data.startswith("set_lang_"))
    dp.callback_query.register(handle_show_favorites, F.data == "show_favorites")
    dp.callback_query.register(handle_show_help, F.data == "show_help")
    dp.callback_query.register(handle_main_menu, F.data == "main_menu")
    dp.callback_query.register(handle_noop, F.data == "noop")
    
    # Коллбэки выбора тарифа
    dp.callback_query.register(handle_buy_premium, F.data == "buy_premium")
    dp.callback_query.register(handle_premium_1_month, F.data == "premium_1_month")
    dp.callback_query.register(handle_premium_3_months, F.data == "premium_3_months")
    dp.callback_query.register(handle_premium_1_year, F.data == "premium_1_year")
    
    # Обработчики оплаты (Stars)
    dp.pre_checkout_query.register(on_pre_checkout_query)
    dp.message.register(on_successful_payment, F.content_type == ContentType.SUCCESSFUL_PAYMENT)
