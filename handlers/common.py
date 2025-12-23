import logging
from aiogram import Dispatcher, F, html
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db 
from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
# Импортируем список языков явно
from config import SUPPORTED_LANGUAGES, ADMIN_IDS, SECRET_PROMO_CODE

logger = logging.getLogger(__name__)

# --- Вспомогательная функция ---
async def track_safely(user_id: int, event_name: str, data: dict = None):
    try:
        await metrics.track_event(user_id, event_name, data)
    except Exception as e:
        logger.error(f"❌ Ошибка метрики ({event_name}): {e}")

# --- START ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    await users_repo.get_or_create(user_id, first_name, username)
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Чистим текст от Markdown (**), чтобы отправить как HTML
    welcome_text = get_text(lang, "welcome", name=html.quote(first_name)).replace("**", "")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_favorites"), callback_data="show_favorites"))
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "btn_change_lang"), callback_data="change_language"),
        InlineKeyboardButton(text=get_text(lang, "btn_help"), callback_data="show_help")
    )
    
    await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await track_safely(user_id, "start_command", {"language": lang})

# --- FAVORITES (COMMAND) ---
async def cmd_favorites(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
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
        builder.row(
            InlineKeyboardButton(text="1", callback_data="noop"),
            InlineKeyboardButton(text="➡️", callback_data="fav_page_2")
        )
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await message.answer(header_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await track_safely(user_id, "favorites_viewed", {"page": 1})

# --- LANG (COMMAND) ---
async def cmd_lang(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    current_lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    builder = InlineKeyboardBuilder()
    # Строим кнопки на основе списка из config.py
    for lang_code in SUPPORTED_LANGUAGES:
        label = get_text(current_lang, f"lang_{lang_code}")
        if lang_code == current_lang:
            label = f"✅ {label}"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"set_lang_{lang_code}"))
    
    builder.row(InlineKeyboardButton(text=get_text(current_lang, "btn_back"), callback_data="main_menu"))
    
    # Красивый заголовок без звездочек
    header = get_text(current_lang, "choose_language").replace("**", "")
    await message.answer(f"<b>{header}</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

# --- HELP (COMMAND) ---
async def cmd_help(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Убираем звездочки Markdown
    title = get_text(lang, 'help_title').replace("**", "")
    text = get_text(lang, 'help_text').replace("*", "")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await message.answer(f"<b>{title}</b>\n\n{text}", reply_markup=builder.as_markup(), parse_mode="HTML")
    await track_safely(user_id, "help_viewed", {"language": lang})

# --- CODE / ADMIN / STATS (Остаются без изменений логики) ---
async def cmd_code(message: Message):
    # Безопасная версия
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Введите код. Пример:\n<code>/code PROMO123</code>", parse_mode="HTML")
        return
    code = args[1].strip()
    if code == SECRET_PROMO_CODE:
        if await users_repo.activate_premium(user_id, 365*99):
            await message.answer("💎 Код принят! Премиум активирован.", parse_mode="HTML")
            await track_safely(user_id, "premium_activated", {"method": "promo"})
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
        builder.row(InlineKeyboardButton(text="💎 Купить премиум", callback_data="buy_premium"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    await message.answer("Админ-панель: /stats, /users, /reset ID")

# --- КОЛЛБЭКИ ---

# 1. СМЕНА ЯЗЫКА (Кнопка в меню)
async def handle_change_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    current_lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    builder = InlineKeyboardBuilder()
    for lang_code in SUPPORTED_LANGUAGES:
        label = get_text(current_lang, f"lang_{lang_code}")
        if lang_code == current_lang:
            label = f"✅ {label}"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"set_lang_{lang_code}"))
    
    builder.row(InlineKeyboardButton(text=get_text(current_lang, "btn_back"), callback_data="main_menu"))
    
    header = get_text(current_lang, "choose_language").replace("**", "")
    await callback.message.edit_text(f"<b>{header}</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

# 2. УСТАНОВКА ЯЗЫКА
async def handle_set_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[2]
    
    await users_repo.update_language(user_id, lang_code)
    
    # Обновляем меню на новом языке
    final_lang = lang_code
    first_name = callback.from_user.first_name
    welcome_text = get_text(final_lang, "welcome", name=html.quote(first_name)).replace("**", "")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(final_lang, "btn_favorites"), callback_data="show_favorites"))
    builder.row(
        InlineKeyboardButton(text=get_text(final_lang, "btn_change_lang"), callback_data="change_language"),
        InlineKeyboardButton(text=get_text(final_lang, "btn_help"), callback_data="show_help")
    )
    
    await callback.message.edit_text(welcome_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await track_safely(user_id, "language_changed", {"language": lang_code})
    await callback.answer(get_text(final_lang, "lang_changed"))

async def handle_show_favorites(callback: CallbackQuery):
    # Перенаправляем на логику показа избранного (упрощенно - вызываем то же самое, что и в /favorites)
    # Но так как это callback, нам нужно редактировать сообщение
    # Для простоты используем ту же логику генерации кнопок, что и в favorites.py handle_favorite_pagination
    # Но этот хендлер - заглушка в common.py, чтобы кнопка в меню работала.
    # ВАЖНО: Основная логика избранного лежит в handlers/favorites.py.
    # Здесь мы просто вызываем "первую страницу".
    from handlers.favorites import handle_favorite_pagination
    # Подменяем data чтобы выглядело как запрос первой страницы
    callback.data = "fav_page_1"
    await handle_favorite_pagination(callback)

async def handle_show_help(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    title = get_text(lang, 'help_title').replace("**", "")
    text = get_text(lang, 'help_text').replace("*", "")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await callback.message.edit_text(f"<b>{title}</b>\n\n{text}", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

async def handle_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    welcome = get_text(lang, "welcome", name=html.quote(callback.from_user.first_name)).replace("**", "")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_favorites"), callback_data="show_favorites"))
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "btn_change_lang"), callback_data="change_language"),
        InlineKeyboardButton(text=get_text(lang, "btn_help"), callback_data="show_help")
    )
    
    await callback.message.edit_text(welcome, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

async def handle_noop(c): await c.answer()

# --- ОПЛАТА (STARS) ---
async def handle_buy_premium(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="1 мес - 100 ⭐️", callback_data="premium_1_month"))
    builder.row(InlineKeyboardButton(text="3 мес - 250 ⭐️", callback_data="premium_3_months"))
    builder.row(InlineKeyboardButton(text="1 год - 800 ⭐️", callback_data="premium_1_year"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"))
    
    await callback.message.edit_text("💎 <b>Премиум</b>\nВыберите тариф:", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

async def handle_premium_1_month(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="Premium (1 мес)", description="30 дней доступа", payload="premium_30_days",
        provider_token="", currency="XTR", prices=[LabeledPrice(label="1 мес", amount=100)]
    )
    await callback.answer()

async def handle_premium_3_months(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="Premium (3 мес)", description="90 дней доступа", payload="premium_90_days",
        provider_token="", currency="XTR", prices=[LabeledPrice(label="3 мес", amount=250)]
    )
    await callback.answer()

async def handle_premium_1_year(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="Premium (1 год)", description="365 дней доступа", payload="premium_365_days",
        provider_token="", currency="XTR", prices=[LabeledPrice(label="1 год", amount=800)]
    )
    await callback.answer()

async def on_pre_checkout_query(q): await q.answer(ok=True)

async def on_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    days = 30 if "30" in payload else (90 if "90" in payload else 365)
    await users_repo.activate_premium(message.from_user.id, days)
    await message.answer(f"🌟 Оплата успешна! Премиум на {days} дней активирован.", parse_mode="HTML")

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