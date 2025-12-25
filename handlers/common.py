import logging
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import html
import re
from datetime import datetime

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
        logger.error(f"❌ Ошибка метрики ({event_name}): {e}", exc_info=True)

def safe_format_text(text: str) -> str:
    if not text: return ""
    text = re.sub(r'#{1,6}\s*(.*?)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    return text

def get_main_menu_keyboard(lang: str, is_premium: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_favorites"), callback_data="show_favorites"))
    if not is_premium:
        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "btn_change_lang"), callback_data="change_language"),
        InlineKeyboardButton(text=get_text(lang, "btn_help"), callback_data="show_help")
    )
    return builder.as_markup()

# --- START / RESTART ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    user_data = await users_repo.get_or_create(user_id, first_name, username)
    lang = user_data.get('language_code', 'en')
    is_premium = user_data.get('is_premium', False)
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(first_name)))
    keyboard = get_main_menu_keyboard(lang, is_premium)
    
    # Если это Callback (нажали Restart), то редактируем, если Message - отправляем
    if isinstance(message, Message):
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
    
    await track_safely(user_id, "start_command", {"language": lang})
    
    if user_data.get('trial_status') == 'pending':
        created_at = user_data.get('created_at')
        if created_at:
            now = datetime.now(created_at.tzinfo)
            if (now - created_at).total_seconds() < 60 and isinstance(message, Message):
                gift_text = safe_format_text(get_text(lang, "welcome_gift_alert"))
                await message.answer(gift_text, parse_mode="HTML")

# !!! НОВАЯ ФУНКЦИЯ ДЛЯ КНОПКИ RESTART !!!
async def handle_restart(callback: CallbackQuery):
    user_id = callback.from_user.id
    # Получаем свежие данные
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    is_premium = user_data.get('is_premium', False)
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(callback.from_user.first_name)))
    keyboard = get_main_menu_keyboard(lang, is_premium)
    
    await callback.message.edit_text(welcome_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# --- FAVORITES ---
async def cmd_favorites(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page=1)
    
    if not favorites:
        await message.answer(get_text(lang, "favorites_empty"))
        return
    
    header_text = safe_format_text(get_text(lang, "favorites_title")) + f" (1/{total_pages})"
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

# --- LANG ---
async def cmd_lang(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    current_lang = user_data.get('language_code', 'en')
    
    builder = InlineKeyboardBuilder()
    for lang_code in SUPPORTED_LANGUAGES:
        label = get_text(current_lang, f"lang_{lang_code}")
        if lang_code == current_lang: label = f"✅ {label}"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"set_lang_{lang_code}"))
    
    builder.row(InlineKeyboardButton(text=get_text(current_lang, "btn_back"), callback_data="main_menu"))
    
    header = safe_format_text(get_text(current_lang, "choose_language"))
    await message.answer(header, reply_markup=builder.as_markup(), parse_mode="HTML")

# --- HELP ---
async def cmd_help(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    title = safe_format_text(get_text(lang, 'help_title'))
    text = safe_format_text(get_text(lang, 'help_text'))
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await message.answer(f"<b>{title}</b>\n\n{text}", reply_markup=builder.as_markup(), parse_mode="HTML")
    await track_safely(user_id, "help_viewed", {"language": lang})

# --- CODE / STATS / ADMIN (Стандарт) ---
async def cmd_code(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Code: <code>/code PROMO123</code>", parse_mode="HTML")
        return
    code = args[1].strip()
    if code == SECRET_PROMO_CODE:
        if await users_repo.activate_premium(user_id, 365*99):
            await message.answer("💎 Success!", parse_mode="HTML")
            await track_safely(user_id, "premium_activated", {"method": "promo"})
            kb = get_main_menu_keyboard(lang, True)
            await message.answer(get_text(lang, "menu"), reply_markup=kb)
    else:
        await message.answer("🚫 Invalid code.")

async def cmd_stats(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    stats = await users_repo.get_usage_stats(user_id)
    if not stats: return
    
    status = "💎 PREMIUM" if stats['is_premium'] else "👤 FREE"
    text = (f"📊 <b>Statistics</b>\n\n{status}\n"
            f"📝 Text: {stats['text_requests_used']}/{stats['text_requests_limit']}\n"
            f"🎤 Voice: {stats['voice_requests_used']}/{stats['voice_requests_limit']}")
            
    builder = InlineKeyboardBuilder()
    if not stats['is_premium']:
        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    await message.answer("Admin: /stats, /users, /reset ID")

# --- КОЛЛБЭКИ ---
async def handle_change_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    current_lang = user_data.get('language_code', 'en')
    
    builder = InlineKeyboardBuilder()
    for lang_code in SUPPORTED_LANGUAGES:
        label = get_text(current_lang, f"lang_{lang_code}")
        if lang_code == current_lang: label = f"✅ {label}"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"set_lang_{lang_code}"))
    builder.row(InlineKeyboardButton(text=get_text(current_lang, "btn_back"), callback_data="main_menu"))
    header = safe_format_text(get_text(current_lang, "choose_language"))
    await callback.message.edit_text(header, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

async def handle_set_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[2]
    await users_repo.update_language(user_id, lang_code)
    
    user_data = await users_repo.get_user(user_id)
    final_lang = lang_code
    
    welcome_text = safe_format_text(get_text(final_lang, "welcome", name=html.quote(callback.from_user.first_name)))
    kb = get_main_menu_keyboard(final_lang, user_data.get('is_premium', False))
    
    await callback.message.edit_text(text=welcome_text, reply_markup=kb, parse_mode="HTML")
    await track_safely(user_id, "language_changed", {"language": lang_code})
    await callback.answer(get_text(final_lang, "lang_changed"))

async def handle_show_favorites(callback: CallbackQuery):
    from handlers.favorites import handle_favorite_pagination
    callback.data = "fav_page_1"
    await handle_favorite_pagination(callback)

async def handle_show_help(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    title = safe_format_text(get_text(lang, 'help_title'))
    text = safe_format_text(get_text(lang, 'help_text'))
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await callback.message.edit_text(f"<b>{title}</b>\n\n{text}", reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

async def handle_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    welcome = safe_format_text(get_text(lang, "welcome", name=html.quote(callback.from_user.first_name)))
    kb = get_main_menu_keyboard(lang, user_data.get('is_premium', False))
    await callback.message.edit_text(text=welcome, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

async def handle_noop(c): await c.answer()

# --- ОПЛАТА ---
async def handle_buy_premium(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="1 Month - 100 ⭐️", callback_data="premium_1_month"))
    builder.row(InlineKeyboardButton(text="3 Months - 250 ⭐️ (-17%)", callback_data="premium_3_months"))
    builder.row(InlineKeyboardButton(text="1 Year - 800 ⭐️ (-33%)", callback_data="premium_1_year"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    desc = safe_format_text(get_text(lang, "premium_description"))
    await callback.message.edit_text(desc, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

async def handle_premium_1_month(c):
    await c.message.answer_invoice(title="Premium 1 Mon", description="30 days", payload="premium_30_days", provider_token="", currency="XTR", prices=[LabeledPrice(label="1", amount=100)])
    await c.answer()
async def handle_premium_3_months(c):
    await c.message.answer_invoice(title="Premium 3 Mon", description="90 days", payload="premium_90_days", provider_token="", currency="XTR", prices=[LabeledPrice(label="3", amount=250)])
    await c.answer()
async def handle_premium_1_year(c):
    await c.message.answer_invoice(title="Premium 1 Year", description="365 days", payload="premium_365_days", provider_token="", currency="XTR", prices=[LabeledPrice(label="1", amount=800)])
    await c.answer()
async def on_pre_checkout_query(q): await q.answer(ok=True)
async def on_successful_payment(m):
    p = m.successful_payment.invoice_payload
    days = 30 if "30" in p else (90 if "90" in p else 365)
    await users_repo.activate_premium(m.from_user.id, days)
    await m.answer(f"🌟 Success! {days} days added.", parse_mode="HTML")

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
    
    # !!! НОВОЕ: РЕГИСТРАЦИЯ RESTART !!!
    dp.callback_query.register(handle_restart, F.data == "restart")