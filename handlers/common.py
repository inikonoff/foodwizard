import logging
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType
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
    try: await metrics.track_event(user_id, event_name, data)
    except: pass

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

def safe_format_text(text: str) -> str:
    if not text: return ""
    text = re.sub(r'#{1,6}\s*(.*?)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    return text

# --- START ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    user_data = await users_repo.get_or_create(user_id, first_name, username)
    lang = user_data.get('language_code', 'en')
    is_premium = user_data.get('is_premium', False)
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(first_name)))
    keyboard = get_main_menu_keyboard(lang, is_premium)
    
    # Отправляем сообщение, если это команда /start, редактируем если рестарт по кнопке
    if isinstance(message, Message):
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
    
    await track_safely(user_id, "start_command", {"language": lang})
    
    if user_data.get('trial_status') == 'pending':
        created_at = user_data.get('created_at')
        if created_at:
            now = datetime.now(created_at.tzinfo)
            if (now - created_at).total_seconds() < 60 and isinstance(message, Message):
                await asyncio.sleep(2)
                gift_text = safe_format_text(get_text(lang, "welcome_gift_alert"))
                await message.answer(gift_text, parse_mode="HTML")

# RESTART BUTTON HANDLER
async def handle_restart(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(callback.from_user.first_name)))
    kb = get_main_menu_keyboard(lang, user_data.get('is_premium', False))
    
    await callback.message.edit_text(welcome_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# --- FAVORITES ---
async def cmd_favorites(message: Message):
    user_id = message.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page=1)
    
    if not favorites:
        await message.answer(get_text(lang, "favorites_empty"))
        return
    
    header = safe_format_text(get_text(lang, "favorites_title")) + f" (1/{total_pages})"
    builder = InlineKeyboardBuilder()
    
    for fav in favorites:
        btn_text = f"{fav['dish_name']} ({fav['created_at'].strftime('%d.%m')})"
        builder.row(InlineKeyboardButton(text=btn_text, callback_data=f"view_fav_{fav['id']}"))
    
    if total_pages > 1:
        builder.row(InlineKeyboardButton(text="1", callback_data="noop"),
                    InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await message.answer(header, reply_markup=builder.as_markup(), parse_mode="HTML")
    await track_safely(user_id, "favorites_viewed", {"page": 1})

async def handle_show_favorites(callback: CallbackQuery):
    # !!! ИСПРАВЛЕНИЕ ОШИБКИ FROZEN INSTANCE !!!
    # Мы не меняем callback.data. Мы просто вызываем функцию,
    # а она сама разберется, что если нет страницы - открываем первую.
    from handlers.favorites import handle_favorite_pagination
    await handle_favorite_pagination(callback)

# ... (Остальные стандартные хендлеры LANG, HELP, CODE и т.д. без изменений) ...

async def cmd_lang(message: Message):
    user_id = message.from_user.id
    current_lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    builder = InlineKeyboardBuilder()
    for l_code in SUPPORTED_LANGUAGES:
        lbl = get_text(current_lang, f"lang_{l_code}")
        if l_code == current_lang: lbl = f"✅ {lbl}"
        builder.row(InlineKeyboardButton(text=lbl, callback_data=f"set_lang_{l_code}"))
    builder.row(InlineKeyboardButton(text=get_text(current_lang, "btn_back"), callback_data="main_menu"))
    header = safe_format_text(get_text(current_lang, "choose_language"))
    await message.answer(header, reply_markup=builder.as_markup(), parse_mode="HTML")

async def cmd_help(message: Message):
    user_id = message.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    t = safe_format_text(get_text(lang, 'help_title'))
    tx = safe_format_text(get_text(lang, 'help_text'))
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await message.answer(f"<b>{t}</b>\n\n{tx}", reply_markup=builder.as_markup(), parse_mode="HTML")
    await track_safely(user_id, "help_viewed", {"language": lang})

async def cmd_code(message: Message):
    uid = message.from_user.id
    args = message.text.split()
    if len(args) < 2: 
        await message.answer("Code: <code>/code PROMO123</code>", parse_mode="HTML")
        return
    if args[1].strip() == SECRET_PROMO_CODE:
        await users_repo.activate_premium(uid, 365*99)
        await message.answer("💎 Success!", parse_mode="HTML")
        # Обновляем меню
        lang = (await users_repo.get_user(uid)).get('language_code', 'en')
        await message.answer(get_text(lang, "menu"), reply_markup=get_main_menu_keyboard(lang, True))
    else: await message.answer("🚫 Invalid")

async def cmd_stats(message: Message):
    uid = message.from_user.id
    st = await users_repo.get_usage_stats(uid)
    if not st: return
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    stat = "💎 PREMIUM" if st['is_premium'] else "👤 FREE"
    txt = (f"📊 <b>Stats</b>\n\n{stat}\n📝 Text: {st['text_requests_used']}/{st['text_requests_limit']}\n"
           f"🎤 Voice: {st['voice_requests_used']}/{st['voice_requests_limit']}")
    b = InlineKeyboardBuilder()
    if not st['is_premium']: b.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await message.answer(txt, reply_markup=b.as_markup(), parse_mode="HTML")

async def cmd_admin(message: Message):
    if message.from_user.id in ADMIN_IDS: await message.answer("Admin commands: /stats, /users, /reset ID")

async def handle_change_language(c): await cmd_lang(c.message)

async def handle_set_language(c: CallbackQuery):
    lang_code = c.data.split("_")[2]
    await users_repo.update_language(c.from_user.id, lang_code)
    uid = c.from_user.id
    ud = await users_repo.get_user(uid)
    w = safe_format_text(get_text(lang_code, "welcome", name=html.quote(c.from_user.first_name)))
    kb = get_main_menu_keyboard(lang_code, ud.get('is_premium', False))
    await c.message.edit_text(w, reply_markup=kb, parse_mode="HTML")
    await c.answer(get_text(lang_code, "lang_changed"))

async def handle_show_help(c): 
    # Повтор логики cmd_help, но с edit_text
    lang = (await users_repo.get_user(c.from_user.id)).get('language_code', 'en')
    t = safe_format_text(get_text(lang, 'help_title'))
    tx = safe_format_text(get_text(lang, 'help_text'))
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await c.message.edit_text(f"<b>{t}</b>\n\n{tx}", reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_main_menu(c: CallbackQuery):
    uid = c.from_user.id
    ud = await users_repo.get_user(uid)
    lang = ud.get('language_code', 'en')
    w = safe_format_text(get_text(lang, "welcome", name=html.quote(c.from_user.first_name)))
    kb = get_main_menu_keyboard(lang, ud.get('is_premium', False))
    await c.message.edit_text(w, reply_markup=kb, parse_mode="HTML")

async def handle_noop(c): await c.answer()

async def handle_buy_premium(c: CallbackQuery):
    lang = (await users_repo.get_user(c.from_user.id)).get('language_code', 'en')
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="1 Mon - 100 ⭐️", callback_data="premium_1_month"))
    b.row(InlineKeyboardButton(text="3 Mon - 250 ⭐️", callback_data="premium_3_months"))
    b.row(InlineKeyboardButton(text="1 Year - 800 ⭐️", callback_data="premium_1_year"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    d = safe_format_text(get_text(lang, "premium_description"))
    await c.message.edit_text(d, reply_markup=b.as_markup(), parse_mode="HTML")

# Оплата Stars - заглушки с функционалом
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
    days = 30
    if "90" in p: days = 90
    if "365" in p: days = 365
    await users_repo.activate_premium(m.from_user.id, days)
    lang = (await users_repo.get_user(m.from_user.id)).get('language_code', 'en')
    kb = get_main_menu_keyboard(lang, True)
    await m.answer(f"🌟 Success! {days} days added.", reply_markup=kb)

def register_common_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_favorites, Command("favorites"))
    dp.message.register(cmd_lang, Command("lang"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_code, Command("code"))
    dp.message.register(cmd_stats, Command("stats"))
    dp.message.register(cmd_admin, Command("admin"))
    
    dp.callback_query.register(handle_restart, F.data == "restart")
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
