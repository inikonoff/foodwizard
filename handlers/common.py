import logging
import asyncio
from datetime import datetime
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, PreCheckoutQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import html
import re

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
    """Убираем Markdown **, чтобы не ломать HTML"""
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

# --- START ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    # --- ЛОГИКА АВТО-ОПРЕДЕЛЕНИЯ ЯЗЫКА ---
    # Получаем язык интерфейса Телеграма (например 'de', 'ru', 'fr')
    detected_lang = message.from_user.language_code
    
    # Если это русский -> меняем на английский (так как русского в боте нет)
    if detected_lang == 'ru':
        lang_to_save = 'en'
    # Если этот язык поддерживается ботом (de, fr, it, es, en) -> используем его
    elif detected_lang in SUPPORTED_LANGUAGES:
        lang_to_save = detected_lang
    else:
        # Иначе (например, китайский) -> английский
        lang_to_save = 'en'
    
    # Создаем или обновляем пользователя с НУЖНЫМ языком
    user_data = await users_repo.get_or_create(user_id, first_name, username, language=lang_to_save)
    # И принудительно обновляем в базе, если юзер уже был (get_or_create может вернуть старый язык)
    await users_repo.update_language(user_id, lang_to_save)
    
    lang = lang_to_save
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(first_name)))
    await message.answer(welcome_text, parse_mode="HTML")
    await track_safely(user_id, "start_command", {"language": lang, "detected": detected_lang})
    
    # ПОДАРОК (ТРИАЛ)
    if user_data.get('trial_status') == 'pending':
        created_at = user_data.get('created_at')
        if created_at:
            now = datetime.now(created_at.tzinfo)
            if (now - created_at).total_seconds() < 120:
                await asyncio.sleep(2)
                await message.answer(safe_format_text(get_text(lang, "welcome_gift_alert")), parse_mode="HTML")

# --- RESTART ---
async def handle_restart(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(callback.from_user.first_name)))
    
    # При рестарте просто редактируем текст и убираем кнопки (reply_markup=None)
    try: await callback.message.edit_text(welcome_text, reply_markup=None, parse_mode="HTML")
    except: await callback.message.answer(welcome_text, reply_markup=None, parse_mode="HTML")
    await callback.answer()

async def handle_main_menu(callback: CallbackQuery):
    # А вот тут кнопки НУЖНЫ
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    kb = get_main_menu_keyboard(lang, user_data.get('is_premium', False))
    txt = safe_format_text(get_text(lang, "menu"))
    try: await callback.message.edit_text(txt, reply_markup=kb, parse_mode="HTML")
    except: await callback.message.answer(txt, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# --- LANG ---
async def cmd_lang(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    builder = InlineKeyboardBuilder()
    for l_code in SUPPORTED_LANGUAGES:
        # Получаем название языка из texts.py
        lbl = get_text(lang, f"lang_{l_code}")
        # Если почему-то ключа нет, фоллбэк на код
        if not lbl or "lang_" in lbl: lbl = l_code.upper()
            
        if l_code == lang: lbl = f"✅ {lbl}"
        builder.row(InlineKeyboardButton(text=lbl, callback_data=f"set_lang_{l_code}"))
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    header = safe_format_text(get_text(lang, "choose_language"))
    await message.answer(header, reply_markup=builder.as_markup(), parse_mode="HTML")

async def handle_change_language(c): await cmd_lang(c.message)

async def handle_set_language(c: CallbackQuery):
    l_code = c.data.split("_")[2]
    await users_repo.update_language(c.from_user.id, l_code)
    
    # Сразу обновляем экран, используя НОВЫЙ язык
    final_lang = l_code
    first_name = c.from_user.first_name
    welcome_text = safe_format_text(get_text(final_lang, "welcome", name=html.quote(first_name)))
    
    # Убираем кнопки (чистый вид)
    await c.message.edit_text(text=welcome_text, reply_markup=None, parse_mode="HTML")
    
    await track_safely(c.from_user.id, "language_changed", {"language": l_code})
    await c.answer(get_text(final_lang, "lang_changed"))

# ... (ОСТАЛЬНЫЕ ФУНКЦИИ БЕЗ ИЗМЕНЕНИЙ) ...
# Копируйте favorites, help, code, admin, stats, buy_premium из прошлого рабочего варианта.
# Изменился только cmd_start, handle_set_language, cmd_lang.

async def cmd_favorites(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    favs, p = await favorites_repo.get_favorites_page(uid, 1)
    if not favs:
        await m.answer(get_text(lang, "favorites_empty"))
        return
    h = safe_format_text(get_text(lang, "favorites_title")) + f" (1/{p})"
    b = InlineKeyboardBuilder()
    for f in favs:
        b.row(InlineKeyboardButton(text=f"{f['dish_name']} ({f['created_at'].strftime('%d.%m')})", callback_data=f"view_fav_{f['id']}"))
    if p>1: b.row(InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(h, reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_show_favorites(c):
    from handlers.favorites import handle_favorite_pagination
    c.data = "fav_page_1"
    await handle_favorite_pagination(c)

async def cmd_help(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    t = safe_format_text(get_text(lang, 'help_title'))
    tx = safe_format_text(get_text(lang, 'help_text'))
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(f"<b>{t}</b>\n\n{tx}", reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_show_help(c): await cmd_help(c.message)

async def cmd_code(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    args = m.text.split()
    if len(args)<2: 
        await m.answer(safe_format_text(get_text(lang, "promo_instruction")), parse_mode="HTML")
        return
    if args[1].strip() == SECRET_PROMO_CODE:
        await users_repo.activate_premium(uid, 365*99)
        await m.answer("💎 Success!")
    else: await m.answer("🚫 Invalid")

async def cmd_stats(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    st = await users_repo.get_usage_stats(uid)
    s = "💎 PREMIUM" if st.get('is_premium') else "👤 FREE"
    t = (f"📊 <b>Statistics</b>\n\n{s}\nText: {st['text_requests_used']}\nVoice: {st['voice_requests_used']}")
    b = InlineKeyboardBuilder()
    if not st.get('is_premium'): b.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(t, reply_markup=b.as_markup(), parse_mode="HTML")

async def cmd_admin(m):
    if m.from_user.id in ADMIN_IDS: await m.answer("Admin OK")
async def handle_noop(c): await c.answer()

async def handle_buy_premium(c):
    lang = (await users_repo.get_user(c.from_user.id)).get('language_code', 'en')
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="1 Mon - 100 ⭐️", callback_data="premium_1_month"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await c.message.edit_text(safe_format_text(get_text(lang, "premium_description")), reply_markup=b.as_markup(), parse_mode="HTML")
async def handle_premium_1_month(c): await c.message.answer_invoice("Prem", "30 days", "30", "", "XTR", [LabeledPrice(label="1", amount=100)])
async def handle_premium_3_months(c): await c.message.answer_invoice("Prem", "90 days", "90", "", "XTR", [LabeledPrice(label="1", amount=250)])
async def handle_premium_1_year(c): await c.message.answer_invoice("Prem", "365 days", "365", "", "XTR", [LabeledPrice(label="1", amount=800)])
async def on_pre(q): await q.answer(ok=True)
async def on_pay(m): await users_repo.activate_premium(m.from_user.id, 30); await m.answer("Success!")

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
    dp.callback_query.register(handle_restart, F.data == "restart")
    dp.callback_query.register(handle_noop, F.data == "noop")
    dp.callback_query.register(handle_buy_premium, F.data == "buy_premium")
    dp.callback_query.register(handle_premium_1_month, F.data == "premium_1_month")
    dp.callback_query.register(handle_premium_3_months, F.data == "premium_3_months")
    dp.callback_query.register(handle_premium_1_year, F.data == "premium_1_year")
    dp.pre_checkout_query.register(on_pre)
    dp.message.register(on_pay, F.content_type == ContentType.SUCCESSFUL_PAYMENT)