import logging
import asyncio
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, PreCheckoutQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import html
import re
from datetime import datetime, timezone

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

# --- START (AUTO DETECT LANGUAGE + CLEAN UI) ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    # 1. Автоопределение языка из Телеграма
    tg_lang = message.from_user.language_code
    if tg_lang and tg_lang in SUPPORTED_LANGUAGES:
        lang_to_save = tg_lang
    else:
        lang_to_save = 'en'
    
    # Сохраняем юзера сразу с нужным языком (или обновляем)
    await users_repo.get_or_create(user_id, first_name, username, language=lang_to_save)
    
    # Получаем актуальные данные (на всякий случай)
    user_data = await users_repo.get_user(user_id)
    # Используем язык, который только что определили
    lang = user_data.get('language_code', lang_to_save)
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(first_name)))
    
    # БЕЗ КНОПОК
    await message.answer(welcome_text, parse_mode="HTML")
    
    await track_safely(user_id, "start_command", {"language": lang, "detected": tg_lang})
    
    # Gift Logic
    if user_data.get('trial_status') == 'pending':
        created_at = user_data.get('created_at')
        if created_at:
            now = datetime.now(created_at.tzinfo)
            if (now - created_at).total_seconds() < 120:
                await asyncio.sleep(2)
                await message.answer(safe_format_text(get_text(lang, "welcome_gift_alert")), parse_mode="HTML")

# --- SET LANGUAGE (CLEAN UI) ---
async def handle_set_language(c: CallbackQuery):
    l_code = c.data.split("_")[2]
    await users_repo.update_language(c.from_user.id, l_code)
    
    final_lang = l_code
    # Используем WELCOME текст, а не слово "Menu"
    welcome_text = safe_format_text(get_text(final_lang, "welcome", name=html.quote(c.from_user.first_name)))
    
    # УБИРАЕМ КНОПКИ (reply_markup=None) - Чистый экран
    await c.message.edit_text(text=welcome_text, reply_markup=None, parse_mode="HTML")
    
    await track_safely(c.from_user.id, "language_changed", {"language": l_code})
    await c.answer(get_text(final_lang, "lang_changed"))

# --- SHOW FAVORITES (FROZEN FIX) ---
async def handle_show_favorites(c: CallbackQuery):
    from handlers.favorites import handle_favorite_pagination
    # МЫ НЕ МЕНЯЕМ c.data. Просто вызываем функцию.
    # Она увидит "show_favorites", не найдет номера страницы и откроет 1-ю.
    await handle_favorite_pagination(c)

# --- RESTART (CLEAN UI) ---
async def handle_restart(c: CallbackQuery):
    uid = c.from_user.id
    ud = await users_repo.get_user(uid)
    lang = ud.get('language_code', 'en')
    w = safe_format_text(get_text(lang, "welcome", name=html.quote(c.from_user.first_name)))
    
    # При рестарте тоже убираем кнопки, чтобы было как при /start
    try: await c.message.edit_text(w, reply_markup=None, parse_mode="HTML")
    except: await c.message.answer(w, parse_mode="HTML")
    await c.answer()

# --- Остальное (Help, Stats, Admin, Pay...) ---

async def handle_main_menu(c): 
    # Кнопка Back в меню должна возвращать главное меню с кнопками
    uid = c.from_user.id
    ud = await users_repo.get_user(uid)
    lang = ud.get('language_code', 'en')
    # Используем заголовок "Menu", так как тут нужны кнопки
    txt = safe_format_text(get_text(lang, "menu"))
    kb = get_main_menu_keyboard(lang, ud.get('is_premium', False))
    try: await c.message.edit_text(txt, reply_markup=kb, parse_mode="HTML")
    except: await c.message.answer(txt, reply_markup=kb, parse_mode="HTML")
    await c.answer()

async def cmd_favorites(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    favs, p = await favorites_repo.get_favorites_page(uid, 1)
    if not favs:
        await m.answer(get_text(lang, "favorites_empty"))
        return
    head = safe_format_text(get_text(lang, "favorites_title")) + f" (1/{p})"
    b = InlineKeyboardBuilder()
    for f in favs:
        date_str = f['created_at'].strftime('%d.%m') if f.get('created_at') else ""
        b.row(InlineKeyboardButton(text=f"{f['dish_name']} ({date_str})", callback_data=f"view_fav_{f['id']}"))
    if p>1: b.row(InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(head, reply_markup=b.as_markup(), parse_mode="HTML")

async def cmd_lang(m): 
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    b = InlineKeyboardBuilder()
    for l in SUPPORTED_LANGUAGES:
        lbl = get_text(lang, f"lang_{l}")
        if l == lang: lbl = f"✅ {lbl}"
        b.row(InlineKeyboardButton(text=lbl, callback_data=f"set_lang_{l}"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(safe_format_text(get_text(lang, "choose_language")), reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_change_language(c): await cmd_lang(c.message)

async def cmd_help(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    t = safe_format_text(get_text(lang, 'help_title'))
    tx = safe_format_text(get_text(lang, 'help_text'))
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(f"<b>{t}</b>\n\n{tx}", reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_show_help(c): 
    uid = c.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    t = safe_format_text(get_text(lang, 'help_title'))
    tx = safe_format_text(get_text(lang, 'help_text'))
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await c.message.edit_text(f"<b>{t}</b>\n\n{tx}", reply_markup=b.as_markup(), parse_mode="HTML")

async def cmd_code(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    args = m.text.split()
    if len(args)<2: 
        await m.answer(safe_format_text(get_text(lang, "promo_instruction")), parse_mode="HTML")
        return
    if args[1].strip() == SECRET_PROMO_CODE:
        if await users_repo.activate_premium(uid, 365*99):
            await m.answer("💎 Success!", parse_mode="HTML")
            await track_safely(uid, "premium_activated", {"method": "promo"})
    else: await m.answer("🚫 Invalid code.")

async def cmd_stats(m):
    uid = m.from_user.id
    st = await users_repo.get_usage_stats(uid)
    if not st: return
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    stat = "💎 PREMIUM" if st.get('is_premium') else "👤 FREE"
    txt = f"📊 <b>Statistics</b>\n\n{stat}\nTXT: {st['text_requests_used']}/{st['text_requests_limit']}\nVOICE: {st['voice_requests_used']}/{st['voice_requests_limit']}"
    b = InlineKeyboardBuilder()
    if not st.get('is_premium'): b.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(txt, reply_markup=b.as_markup(), parse_mode="HTML")

async def cmd_admin(m):
    if m.from_user.id in ADMIN_IDS: await m.answer("Admin: /stats, /users, /reset ID")

async def handle_buy_premium(c: CallbackQuery):
    lang = (await users_repo.get_user(c.from_user.id)).get('language_code', 'en')
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="1 Mon - 100 ⭐️", callback_data="premium_1_month"))
    b.row(InlineKeyboardButton(text="3 Mon - 250 ⭐️ (-17%)", callback_data="premium_3_months"))
    b.row(InlineKeyboardButton(text="1 Year - 800 ⭐️ (-33%)", callback_data="premium_1_year"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await c.message.edit_text(safe_format_text(get_text(lang, "premium_description")), reply_markup=b.as_markup(), parse_mode="HTML")
    await c.answer()

# Payment Logic (Stubs or Real)
async def handle_premium_buy_action(c):
    await c.message.answer_invoice("Premium", "Access", c.data, "", "XTR", [LabeledPrice(label="P", amount=100 if "1" in c.data else 250)])
    await c.answer()

async def on_pre_checkout_query(q): await q.answer(ok=True)
async def on_successful_payment(m):
    p = m.successful_payment.invoice_payload
    days = 30
    if "90" in p: days = 90
    elif "365" in p: days = 365
    await users_repo.activate_premium(m.from_user.id, days)
    for adm in ADMIN_IDS:
        try: await m.bot.send_message(adm, f"💰 Sale! {days} days")
        except: pass
    await m.answer(f"🌟 Success! {days} days.")

async def handle_noop(c): await c.answer()

def register_common_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_favorites, Command("favorites"))
    dp.message.register(cmd_lang, Command("lang"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_code, Command("code"))
    dp.message.register(cmd_stats, Command("stats"))
    dp.message.register(cmd_admin, Command("admin"))
    
    dp.callback_query.register(handle_restart, F.data == "restart")
    dp.callback_query.register(handle_main_menu, F.data == "main_menu")
    dp.callback_query.register(handle_change_language, F.data == "change_language")
    dp.callback_query.register(handle_set_language, F.data.startswith("set_lang_"))
    dp.callback_query.register(handle_show_favorites, F.data == "show_favorites")
    dp.callback_query.register(handle_show_help, F.data == "show_help")
    dp.callback_query.register(handle_noop, F.data == "noop")
    dp.callback_query.register(handle_buy_premium, F.data == "buy_premium")
    # Generic Premium Handler to save space
    dp.callback_query.register(handle_premium_buy_action, F.data.startswith("premium_"))
    dp.pre_checkout_query.register(on_pre_checkout_query)
    dp.message.register(on_successful_payment, F.content_type == ContentType.SUCCESSFUL_PAYMENT)
