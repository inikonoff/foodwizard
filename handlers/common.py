import logging
import re
import asyncio # <--- ЭТОГО НЕ ХВАТАЛО!
from datetime import datetime, timezone # Timezone для сравнения времени
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import html

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
    # Очищаем Markdown (**) чтобы не конфликтовал с HTML
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
    
    # 1. Определяем язык (Telegram lang)
    tg_lang = message.from_user.language_code
    default_lang = 'en'
    if tg_lang:
        short = tg_lang[:2]
        if short in SUPPORTED_LANGUAGES: default_lang = short

    # 2. Создаем/обновляем юзера
    user_data = await users_repo.get_or_create(user_id, first_name, username, language=default_lang)
    
    # 3. Актуализируем язык
    current_lang = user_data.get('language_code')
    lang = current_lang if current_lang in SUPPORTED_LANGUAGES else default_lang

    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(first_name)))
    await message.answer(welcome_text, parse_mode="HTML")
    await track_safely(user_id, "start_command", {"language": lang})
    
    # 4. ПОДАРОК (Требует import asyncio и timezone!)
    if user_data.get('trial_status') == 'pending':
        created_at = user_data.get('created_at')
        if created_at:
            if created_at.tzinfo is None: created_at = created_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            # Если юзер создан < 120 сек назад -> шлем алерт
            if abs((now - created_at).total_seconds()) < 120:
                await asyncio.sleep(2) 
                gift_text = safe_format_text(get_text(lang, "welcome_gift_alert"))
                await message.answer(gift_text, parse_mode="HTML")

# --- COMMANDS ---
async def cmd_lang(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    # Если юзер удален из БД, но нажал команду -> фоллбэк на EN
    lang = user_data.get('language_code', 'en') if user_data else 'en'
    
    builder = InlineKeyboardBuilder()
    for l_code in SUPPORTED_LANGUAGES:
        label = get_text(lang, f"lang_{l_code}")
        if not label: label = l_code.upper() # Fallback
        
        if l_code == lang: label = f"✅ {label}"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"set_lang_{l_code}"))
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    # ВОТ ЗДЕСЬ БЫЛА ОШИБКА, ЕСЛИ "choose_language" НЕТ В СЛОВАРЕ
    header_raw = get_text(lang, "choose_language")
    if not header_raw: header_raw = "Choose Language:" # Аварийный текст
    
    header = safe_format_text(header_raw)
    await message.answer(header, reply_markup=builder.as_markup(), parse_mode="HTML")

async def cmd_favorites(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en') if user_data else 'en'
    
    favorites, pages = await favorites_repo.get_favorites_page(user_id, 1)
    if not favorites:
        await message.answer(get_text(lang, "favorites_empty"))
        return
    
    header_text = safe_format_text(get_text(lang, "favorites_title")) + f" (1/{pages})"
    b = InlineKeyboardBuilder()
    for fav in favorites:
        b.row(InlineKeyboardButton(text=f"{fav['dish_name']} ({fav['created_at'].strftime('%d.%m')})", callback_data=f"view_fav_{fav['id']}"))
    if pages > 1:
        b.row(InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await message.answer(header_text, reply_markup=b.as_markup(), parse_mode="HTML")
    await track_safely(user_id, "favorites_viewed", {"page": 1})

async def cmd_help(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en') if user_data else 'en'
    
    title = safe_format_text(get_text(lang, 'help_title'))
    text = safe_format_text(get_text(lang, 'help_text'))
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await message.answer(f"<b>{title}</b>\n\n{text}", reply_markup=builder.as_markup(), parse_mode="HTML")

async def cmd_code(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en') if user_data else 'en'
    
    args = message.text.split()
    if len(args) < 2:
        instr = get_text(lang, "promo_instruction")
        await message.answer(safe_format_text(instr), parse_mode="HTML")
        return
    
    code = args[1].strip()
    if code == SECRET_PROMO_CODE:
        await users_repo.activate_premium(user_id, 365*99)
        await message.answer("💎 Success!", parse_mode="HTML")
        kb = get_main_menu_keyboard(lang, True)
        await message.answer(get_text(lang, "menu"), reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer("🚫 Invalid")

async def cmd_stats(message: Message):
    uid = message.from_user.id
    st = await users_repo.get_usage_stats(uid)
    if not st: 
        await message.answer("No data")
        return
    lang = (await users_repo.get_user(uid) or {}).get('language_code', 'en')
    s = "💎 PREMIUM" if st.get('is_premium') else "👤 FREE"
    t = (f"📊 <b>Statistics</b>\n\n{s}\n📝 Text: {st['text_requests_used']}/{st['text_requests_limit']}\n🎤 Voice: {st['voice_requests_used']}/{st['voice_requests_limit']}")
    b = InlineKeyboardBuilder()
    if not st.get('is_premium'): b.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await message.answer(t, reply_markup=b.as_markup(), parse_mode="HTML")

async def cmd_admin(message: Message):
    if message.from_user.id in ADMIN_IDS: await message.answer("Admin: /stats /broadcast")

# --- CALLBACKS ---

async def handle_restart(c: CallbackQuery):
    uid = c.from_user.id
    ud = await users_repo.get_user(uid)
    lang = ud.get('language_code', 'en') if ud else 'en'
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(c.from_user.first_name)))
    # Без кнопок при рестарте!
    try: await c.message.edit_text(welcome_text, reply_markup=None, parse_mode="HTML")
    except: await c.message.answer(welcome_text, reply_markup=None, parse_mode="HTML")
    await c.answer()

async def handle_main_menu(c: CallbackQuery):
    uid = c.from_user.id
    ud = await users_repo.get_user(uid)
    lang = ud.get('language_code', 'en') if ud else 'en'
    kb = get_main_menu_keyboard(lang, ud.get('is_premium', False)) if ud else None
    txt = safe_format_text(get_text(lang, "menu"))
    try: await c.message.edit_text(txt, reply_markup=kb, parse_mode="HTML")
    except: await c.message.answer(txt, reply_markup=kb, parse_mode="HTML")
    await c.answer()

async def handle_show_favorites(c):
    from handlers.favorites import handle_favorite_pagination
    # Симуляция нажатия без параметра страницы -> откроется 1-я
    await handle_favorite_pagination(c)

async def handle_change_language(c: CallbackQuery):
    await cmd_lang(c.message)
    await c.answer()

async def handle_set_language(c: CallbackQuery):
    l = c.data.split("_")[2]
    await users_repo.update_language(c.from_user.id, l)
    
    welcome = safe_format_text(get_text(l, "welcome", name=html.quote(c.from_user.first_name)))
    await c.message.edit_text(welcome, reply_markup=None, parse_mode="HTML")
    
    await track_safely(c.from_user.id, "language_changed", {"lang": l})
    await c.answer(get_text(l, "lang_changed"))

async def handle_show_help(c): await cmd_help(c.message); await c.answer()
async def handle_noop(c): await c.answer()

# --- PAYMENT ---
async def handle_buy_premium(c):
    lang = (await users_repo.get_user(c.from_user.id)).get('language_code', 'en')
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="1 Mon - 100 ⭐️", callback_data="premium_1_month"))
    b.row(InlineKeyboardButton(text="3 Mon - 250 ⭐️ (-17%)", callback_data="premium_3_months"))
    b.row(InlineKeyboardButton(text="1 Year - 800 ⭐️ (-33%)", callback_data="premium_1_year"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    d = safe_format_text(get_text(lang, "premium_description"))
    await c.message.edit_text(d, reply_markup=b.as_markup(), parse_mode="HTML")
    await c.answer()

async def handle_premium_buy(c): 
    # Динамическая обработка
    t = c.data.replace("premium_", "") # 1_month, 3_months...
    price = 100
    if "3_months" in t: price = 250
    elif "1_year" in t: price = 800
    await c.message.answer_invoice("Premium", "Access", t, "", "XTR", [LabeledPrice(label="Plan", amount=price)])
    await c.answer()

async def on_pre(q): await q.answer(ok=True)
async def on_pay(m):
    p = m.successful_payment.invoice_payload
    d = 30
    if "90" in p or "3_months" in p: d = 90
    elif "365" in p or "1_year" in p: d = 365
    await users_repo.activate_premium(m.from_user.id, d)
    name = html.quote(m.from_user.full_name)
    for adm in ADMIN_IDS:
        try: await m.bot.send_message(adm, f"💰 Sale! {name}: {d} days")
        except: pass
    kb = get_main_menu_keyboard('en', True) # Простая заглушка языка
    await m.answer("💎 Activated!", reply_markup=kb)

# REGISTER
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
    dp.callback_query.register(handle_premium_buy, F.data.startswith("premium_")) # Универсальный хендлер для 3 кнопок
    
    dp.pre_checkout_query.register(on_pre)
    dp.message.register(on_pay, F.content_type == ContentType.SUCCESSFUL_PAYMENT)