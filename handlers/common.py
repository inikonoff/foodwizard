import logging
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

async def track_safely(user_id: int, event_name: str, data: dict = None):
    try:
        await metrics.track_event(user_id, event_name, data)
    except Exception as e:
        logger.error(f"❌ Ошибка метрики ({event_name}): {e}")

# --- ФУНКЦИЯ СОЗДАНИЯ ГЛАВНОГО МЕНЮ ---
def get_main_menu_keyboard(lang: str, is_premium: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Кнопка Избранное (работает для всех, но внутри проверка)
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_favorites"), callback_data="show_favorites"))

    # Кнопка Премиум (ТОЛЬКО ЕСЛИ НЕТ ПРЕМИУМА)
    if not is_premium:
        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "btn_change_lang"), callback_data="change_language"),
        InlineKeyboardButton(text=get_text(lang, "btn_help"), callback_data="show_help")
    )
    return builder.as_markup()

# --- START ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    user_data = await users_repo.get_or_create(user_id, first_name, username)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    is_premium = user_data.get('is_premium', False)
    
    # Формируем приветствие (чистим от Markdown **)
    welcome_text = get_text(lang, "welcome", name=first_name).replace("**", "")
    
    # Используем общую функцию меню
    keyboard = get_main_menu_keyboard(lang, is_premium)
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
    await track_safely(user_id, "start_command", {"language": lang})

# --- FAVORITES (COMMAND) - БЛОКИРОВКА ---
async def cmd_favorites(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ПРОВЕРКА ПРЕМИУМА
    if not user_data.get('is_premium', False):
        await show_premium_paywall(message, lang)
        return
    
    # ... логика показа избранного (как и раньше) ...
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page=1)
    
    if not favorites:
        await message.answer(get_text(lang, "favorites_empty"))
        return
    
    header_text = get_text(lang, "favorites_title").replace("**", "") + f" (1/{total_pages})"
    builder = InlineKeyboardBuilder()
    for fav in favorites:
        date_str = fav['created_at'].strftime("%d.%m")
        btn_text = f"{fav['dish_name']} ({date_str})"
        builder.row(InlineKeyboardButton(text=btn_text, callback_data=f"view_fav_{fav['id']}"))
    
    if total_pages > 1:
        builder.row(InlineKeyboardButton(text="1", callback_data="noop"),
                    InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await message.answer(header_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await track_safely(user_id, "favorites_viewed", {"page": 1})

# --- ВСПОМОГАТЕЛЬНАЯ: ПОКАЗ ПЕЙВОЛА ---
async def show_premium_paywall(message_or_callback, lang: str):
    text = get_text(lang, "premium_required_text")
    title = get_text(lang, "premium_required_title").replace("**", "")
    
    full_text = f"<b>{title}</b>\n\n{text}"
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(full_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message_or_callback.message.edit_text(full_text, reply_markup=builder.as_markup(), parse_mode="HTML")


# --- LANG (COMMAND) ---
async def cmd_lang(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    current_lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    builder = InlineKeyboardBuilder()
    for lang_code in SUPPORTED_LANGUAGES:
        label = get_text(current_lang, f"lang_{lang_code}")
        if lang_code == current_lang: label = f"✅ {label}"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"set_lang_{lang_code}"))
    
    builder.row(InlineKeyboardButton(text=get_text(current_lang, "btn_back"), callback_data="main_menu"))
    
    header = get_text(current_lang, "choose_language").replace("**", "")
    await message.answer(f"<b>{header}</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

# --- HELP ---
async def cmd_help(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    title = get_text(lang, 'help_title').replace("**", "")
    text = get_text(lang, 'help_text').replace("*", "")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await message.answer(f"<b>{title}</b>\n\n{text}", reply_markup=builder.as_markup(), parse_mode="HTML")

# --- CODE / ADMIN / STATS ---
async def cmd_code(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Введите код. Пример:\n<code>/code PROMO123</code>", parse_mode="HTML")
        return
    code = args[1].strip()
    if code == SECRET_PROMO_CODE:
        if await users_repo.activate_premium(user_id, 365*99):
            await message.answer("💎 Код принят! Премиум активирован.", parse_mode="HTML")
            await track_safely(user_id, "premium_activated", {"method": "promo"})
            # Можно отправить новое меню, чтобы пропала кнопка "Купить"
            keyboard = get_main_menu_keyboard(lang, True)
            await message.answer(get_text(lang, "menu"), reply_markup=keyboard)

    else:
        await message.answer("🚫 Неверный код.")

async def cmd_stats(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    stats = await users_repo.get_usage_stats(user_id)
    
    if not stats:
        await message.answer("Нет данных.")
        return
    
    status = "💎 PREMIUM" if stats['is_premium'] else "👤 FREE"
    text = (f"📊 <b>Статистика</b>\n\n{status}\n"
            f"📝 Текст: {stats['text_requests_used']}/{stats['text_requests_limit']}\n"
            f"🎤 Голос: {stats['voice_requests_used']}/{stats['voice_requests_limit']}")
            
    builder = InlineKeyboardBuilder()
    if not stats['is_premium']:
        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    await message.answer("Админ-панель: /stats, /users, /reset ID")


# --- КОЛЛБЭКИ ---

async def handle_change_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    current_lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    builder = InlineKeyboardBuilder()
    for lang_code in SUPPORTED_LANGUAGES:
        label = get_text(current_lang, f"lang_{lang_code}")
        if lang_code == current_lang: label = f"✅ {label}"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"set_lang_{lang_code}"))
    
    builder.row(InlineKeyboardButton(text=get_text(current_lang, "btn_back"), callback_data="main_menu"))
    
    header = get_text(current_lang, "choose_language").replace("**", "")
    await callback.message.edit_text(f"<b>{header}</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

async def handle_set_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[2]
    
    await users_repo.update_language(user_id, lang_code)
    
    user_data = await users_repo.get_user(user_id)
    # Важно: обновляем данные о пользователе для меню
    is_premium = user_data.get('is_premium', False)
    final_lang = lang_code
    first_name = callback.from_user.first_name
    
    welcome_text = get_text(final_lang, "welcome", name=first_name).replace("**", "")
    
    # Генерируем меню с учетом языка и премиума
    keyboard = get_main_menu_keyboard(final_lang, is_premium)
    
    await callback.message.edit_text(text=welcome_text, reply_markup=keyboard, parse_mode="HTML")
    await track_safely(user_id, "language_changed", {"language": lang_code})
    await callback.answer(get_text(final_lang, "lang_changed"))

async def handle_show_favorites(callback: CallbackQuery):
    # ПРОВЕРКА ПРЕМИУМА (Callback версия)
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru')
    
    if not user_data.get('is_premium', False):
        await show_premium_paywall(callback, lang)
        await callback.answer()
        return

    # Если премиум есть - перенаправляем на логику списка
    from handlers.favorites import handle_favorite_pagination
    callback.data = "fav_page_1"
    await handle_favorite_pagination(callback)

async def handle_show_help(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru')
    
    title = get_text(lang, 'help_title').replace("**", "")
    text = get_text(lang, 'help_text').replace("*", "")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await callback.message.edit_text(f"<b>{title}</b>\n\n{text}", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

async def handle_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru')
    is_premium = user_data.get('is_premium', False)
    
    welcome = get_text(lang, "welcome", name=callback.from_user.first_name).replace("**", "")
    
    keyboard = get_main_menu_keyboard(lang, is_premium)
    
    await callback.message.edit_text(text=welcome, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def handle_noop(c): await c.answer()

# ... (начало файла без изменений) ...

# --- ОПЛАТА И ПРЕМИУМ ---
async def handle_buy_premium(callback: CallbackQuery):
    user_id = callback.from_user.id
    # Гарантированно получаем язык
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="1 мес - 100 ⭐️", callback_data="premium_1_month"))
    builder.row(InlineKeyboardButton(text="3 мес - 250 ⭐️ (-17%)", callback_data="premium_3_months"))
    builder.row(InlineKeyboardButton(text="1 год - 800 ⭐️ (-33%)", callback_data="premium_1_year"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    try:
        # Получаем описание
        desc = get_text(lang, "premium_description")
        if not desc:
            desc = "💎 Premium / Премиум" # Заглушка, если текст потерялся
        
        # Чистим от Markdown, который может сломать HTML
        desc = desc.replace("**", "<b>").replace("__", "")
        
        await callback.message.edit_text(desc, reply_markup=builder.as_markup(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка отображения премиум меню: {e}")
        # Если не удалось отредактировать (например, из-за картинки или разметки), пробуем отправить новым
        try:
            await callback.message.answer("💎 Premium Plans:", reply_markup=builder.as_markup())
        except:
            pass
    
    await callback.answer()

# Хендлеры оплаты остаются теми же (они корректны)
async def handle_premium_1_month(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="Premium (1 мес)", description="30 дней", payload="premium_30_days",
        provider_token="", currency="XTR", prices=[LabeledPrice(label="1 мес", amount=100)]
    )
    await callback.answer()

async def handle_premium_3_months(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="Premium (3 мес)", description="90 дней", payload="premium_90_days",
        provider_token="", currency="XTR", prices=[LabeledPrice(label="3 мес", amount=250)]
    )
    await callback.answer()

async def handle_premium_1_year(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="Premium (1 год)", description="365 дней", payload="premium_365_days",
        provider_token="", currency="XTR", prices=[LabeledPrice(label="1 год", amount=800)]
    )
    await callback.answer()

async def on_pre_checkout_query(q): await q.answer(ok=True)

async def on_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    days = 30
    if "90" in payload: days = 90
    if "365" in payload: days = 365
    
    await users_repo.activate_premium(message.from_user.id, days)
    # Отправляем сообщение и новое меню (без кнопки купить)
    lang = (await users_repo.get_user(message.from_user.id)).get('language_code', 'ru')
    keyboard = get_main_menu_keyboard(lang, True)
    
    await message.answer(f"🌟 <b>Успех!</b> Премиум на {days} дней активирован.", parse_mode="HTML")
    await message.answer(get_text(lang, "welcome", name=message.from_user.first_name).replace("**", ""), reply_markup=keyboard, parse_mode="HTML")

# --- РЕГИСТРАЦИЯ ---
def register_common_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_favorites, Command("favorites"))
    dp.message.register(cmd_lang, Command("lang"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_code, Command("code"))
    dp.message.register(cmd_stats, Command("stats"))
    dp.message.register(cmd_admin, Command("admin"))
    
    dp.callback_query.register(handle_change_language, F.data == "change_language")
    dp.callback_query.register(handle_set_language, F.data.startswith("set_lang_"))
    dp.callback_query.register(handle_show_favorites, F.data == "show_favorites")
    dp.callback_query.register(handle_show_help, F.data == "show_help")
    dp.callback_query.register(handle_main_menu, F.data == "main_menu")
    dp.callback_query.register(handle_noop, F.data == "noop")
    
    dp.callback_query.register(handle_buy_premium, F.data == "buy_premium")
    dp.callback_query.register(handle_premium_1_month, F.data == "premium_1_month")
    dp.callback_query.register(handle_premium_3_months, F.data == "premium_3_months")
    dp.callback_query.register(handle_premium_1_year, F.data == "premium_1_year")
    
    dp.pre_checkout_query.register(on_pre_checkout_query)
    dp.message.register(on_successful_payment, F.content_type == ContentType.SUCCESSFUL_PAYMENT)