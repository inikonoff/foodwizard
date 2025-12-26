import logging
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import html
import re
from datetime import datetime

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
    # Эта функция строит меню для тех мест, где оно нужно (например, при оплате),
    # НО мы не будем вызывать её для главного экрана "Привет"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_favorites"), callback_data="show_favorites"))
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
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    user_data = await users_repo.get_or_create(user_id, first_name, username)
    lang = user_data.get('language_code', 'en')
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(first_name)))
    
    # 1. ТЕКСТ БЕЗ КНОПОК
    await message.answer(welcome_text, parse_mode="HTML")
    await track_safely(user_id, "start_command", {"language": lang})
    
    # 2. ПОДАРОК
    if user_data.get('trial_status') == 'pending':
        created_at = user_data.get('created_at')
        if created_at and (datetime.now(created_at.tzinfo) - created_at).total_seconds() < 60:
            await asyncio.sleep(2)
            await message.answer(safe_format_text(get_text(lang, "welcome_gift_alert")), parse_mode="HTML")

# --- RESTART (ЧИСТЫЙ) ---
async def handle_restart(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(callback.from_user.first_name)))
    
    # !!! УБРАНЫ КНОПКИ (reply_markup=None) !!!
    # Так как пользователь хочет "вернуться в начало"
    await callback.message.edit_text(welcome_text, reply_markup=None, parse_mode="HTML")
    await callback.answer()

async def handle_main_menu(callback: CallbackQuery):
    await handle_restart(callback)

# --- SET LANGUAGE (ЧИСТЫЙ ПОСЛЕ ВЫБОРА) ---
async def handle_set_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[2]
    await users_repo.update_language(user_id, lang_code)
    
    final_lang = lang_code
    first_name = callback.from_user.first_name
    welcome_text = safe_format_text(get_text(final_lang, "welcome", name=html.quote(first_name)))
    
    # !!! УБРАНЫ КНОПКИ (reply_markup=None) !!!
    await callback.message.edit_text(text=welcome_text, reply_markup=None, parse_mode="HTML")
    
    await track_safely(user_id, "language_changed", {"language": lang_code})
    await callback.answer(get_text(final_lang, "lang_changed"))

# --- ОСТАЛЬНЫЕ (Lang list, Help, Favorites, Code...) БЕЗ ИЗМЕНЕНИЙ ---
# Скопируйте функции cmd_favorites, cmd_lang, cmd_help, cmd_code, cmd_stats, cmd_admin,
# handle_show_favorites, handle_change_language, handle_buy_premium и оплату 
# из ПРЕДЫДУЩЕГО полного сообщения. Они работают корректно. 
# Главное было изменить Start, Restart и Set Language выше.

async def cmd_lang(m):
    # Показать список языков
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    b = InlineKeyboardBuilder()
    for l in SUPPORTED_LANGUAGES:
        lbl = get_text(lang, f"lang_{l}")
        if l == lang: lbl = f"✅ {lbl}"
        b.row(InlineKeyboardButton(text=lbl, callback_data=f"set_lang_{l}"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(safe_format_text(get_text(lang, "choose_language")), reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_change_language(c):
    # Показать список (коллбэк)
    uid = c.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    b = InlineKeyboardBuilder()
    for l in SUPPORTED_LANGUAGES:
        lbl = get_text(lang, f"lang_{l}")
        if l == lang: lbl = f"✅ {lbl}"
        b.row(InlineKeyboardButton(text=lbl, callback_data=f"set_lang_{l}"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await c.message.edit_text(safe_format_text(get_text(lang, "choose_language")), reply_markup=b.as_markup(), parse_mode="HTML")

async def cmd_favorites(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    favs, pages = await favorites_repo.get_favorites_page(uid, 1)
    if not favs:
        await m.answer(get_text(lang, "favorites_empty"))
        return
    head = safe_format_text(get_text(lang, "favorites_title")) + f" (1/{pages})"
    b = InlineKeyboardBuilder()
    for f in favs:
        b.row(InlineKeyboardButton(text=f"{f['dish_name']} ({f['created_at'].strftime('%d.%m')})", callback_data=f"view_fav_{f['id']}"))
    if pages > 1:
        b.row(InlineKeyboardButton(text="1", callback_data="noop"), InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(head, reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_show_favorites(c):
    from handlers.favorites import handle_favorite_pagination
    c.data = "fav_page_1" # Hack to reuse logic
    await handle_favorite_pagination(c)

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

# ... admin/stats/code ...
async def cmd_admin(m):
    if m.from_user.id in ADMIN_IDS: await m.answer("/stats /users")
async def cmd_stats(m):
    uid = m.from_user.id
    st = await users_repo.get_usage_stats(uid)
    if not st: return
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    stat = "💎 PREMIUM" if st['is_premium'] else "👤 FREE"
    t = f"📊 <b>Statistics</b>\n\n{stat}\nTXT: {st['text_requests_used']}\nVOICE: {st['voice_requests_used']}"
    b = InlineKeyboardBuilder()
    if not st['is_premium']: b.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(t, reply_markup=b.as_markup(), parse_mode="HTML")

async def cmd_code(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    args = m.text.split()
    if len(args)<2: 
        await m.answer("Code: <code>PROMO123</code>", parse_mode="HTML")
        return
    if args[1].strip() == SECRET_PROMO_CODE:
        await users_repo.activate_premium(uid, 36500)
        await m.answer("💎 Success!")
    else: await m.answer("Invalid")

async def handle_buy_premium(c):
    lang = (await users_repo.get_user(c.from_user.id)).get('language_code', 'en')
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="1 Mon - 100 ⭐️", callback_data="premium_1_month"))
    b.row(InlineKeyboardButton(text="🔙", callback_data="main_menu"))
    desc = safe_format_text(get_text(lang, "premium_description"))
    await c.message.edit_text(desc, reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_premium_1_month(c):
    await c.message.answer_invoice("Prem", "Desc", "pl", "", "XTR", [LabeledPrice(label="1", amount=100)])
    await c.answer()

# Остальные заглушки оплаты ...
async def handle_premium_3_months(c): await c.answer("TODO")
async def handle_premium_1_year(c): await c.answer("TODO")
async def handle_noop(c): await c.answer()
async def on_pre_checkout_query(q): await q.answer(ok=True)
async def on_successful_payment(m): await users_repo.activate_premium(m.from_user.id, 30); await m.answer("Paid!")

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
    dp.callback_query.register(handle_premium_1_month, F.data == "premium_1_month")
    # ...
    dp.pre_checkout_query.register(on_pre_checkout_query)
    dp.message.register(on_successful_payment, F.content_type == ContentType.SUCCESSFUL_PAYMENT)