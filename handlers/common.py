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

# --- START (ИСПРАВЛЕНА ЛОГИКА ЯЗЫКА) ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    # 1. Определяем язык интерфейса Telegram (например 'de', 'es')
    tg_lang = message.from_user.language_code or 'en'
    if len(tg_lang) > 2: 
        tg_lang = tg_lang[:2] # Превращаем 'en-US' в 'en'

    # 2. Проверяем, поддерживаем ли мы его, иначе 'en'
    detected_lang = tg_lang if tg_lang in SUPPORTED_LANGUAGES else 'en'
    
    # 3. Регистрируем юзера сразу с нужным языком
    # И принудительно обновляем его, если юзер уже был в базе (чтобы язык переключился)
    user_data = await users_repo.get_or_create(user_id, first_name, username, language=detected_lang)
    await users_repo.update_language(user_id, detected_lang)
    
    is_premium = user_data.get('is_premium', False)
    
    # 4. Получаем текст приветствия на ДЕТЕКТИРОВАННОМ языке
    welcome_text = safe_format_text(get_text(detected_lang, "welcome", name=html.quote(first_name)))
    
    await message.answer(welcome_text, parse_mode="HTML")
    await track_safely(user_id, "start_command", {"language": detected_lang})
    
    # Подарок
    if user_data.get('trial_status') == 'pending':
        created_at = user_data.get('created_at')
        if created_at:
            now = datetime.now(created_at.tzinfo)
            if (now - created_at).total_seconds() < 120:
                await asyncio.sleep(2)
                # Подарок тоже на детектированном языке
                await message.answer(safe_format_text(get_text(detected_lang, "welcome_gift_alert")), parse_mode="HTML")

# ... (Остальной код хендлеров: restart, favorites, lang, help, code, admin... БЕЗ ИЗМЕНЕНИЙ) ...
# Я скопирую сокращенные версии для полноты файла, чтобы вы могли просто заменить его.

async def handle_restart(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    welcome = safe_format_text(get_text(lang, "welcome", name=html.quote(callback.from_user.first_name)))
    # Без кнопок (reply_markup=None) для чистоты
    try: await callback.message.edit_text(welcome, reply_markup=None, parse_mode="HTML")
    except: await callback.message.answer(welcome, reply_markup=None, parse_mode="HTML")
    await callback.answer()

async def handle_main_menu(c):
    uid = c.from_user.id
    ud = await users_repo.get_user(uid)
    lang = ud.get('language_code', 'en')
    kb = get_main_menu_keyboard(lang, ud.get('is_premium', False))
    txt = safe_format_text(get_text(lang, "menu"))
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
    for f in favs: b.row(InlineKeyboardButton(text=f"{f['dish_name']} ({f['created_at'].strftime('%d.%m')})", callback_data=f"view_fav_{f['id']}"))
    if p>1: b.row(InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(head, reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_show_favorites(c):
    from handlers.favorites import handle_favorite_pagination
    await handle_favorite_pagination(c)

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
async def handle_set_language(c):
    l = c.data.split("_")[2]
    await users_repo.update_language(c.from_user.id, l)
    w = safe_format_text(get_text(l, "welcome", name=html.quote(c.from_user.first_name)))
    await c.message.edit_text(text=w, reply_markup=None, parse_mode="HTML")
    await track_safely(c.from_user.id, "language_changed", {"lang": l})
    await c.answer(get_text(l, "lang_changed"))

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
        if await users_repo.activate_premium(uid, 365*99):
            await m.answer("💎 Success!")
    else: await m.answer("🚫 Invalid")

async def cmd_stats(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    st = await users_repo.get_usage_stats(uid)
    s = "💎 PREMIUM" if st.get('is_premium') else "👤 FREE"
    t = (f"📊 <b>Statistics</b>\n\n{s}\nText: {st['text_requests_used']}/{st['text_requests_limit']}\nVoice: {st['voice_requests_used']}/{st['voice_requests_limit']}")
    b = InlineKeyboardBuilder()
    if not st.get('is_premium'): b.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(t, reply_markup=b.as_markup(), parse_mode="HTML")

async def cmd_admin(m):
    if m.from_user.id in ADMIN_IDS: await m.answer("Admin OK")

async def handle_noop(c): await c.answer()

# --- ОПЛАТА ---
async def handle_buy_premium(c):
    lang = (await users_repo.get_user(c.from_user.id)).get('language_code', 'en')
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="1 Mon - 100 ⭐️", callback_data="premium_1_month"))
    b.row(InlineKeyboardButton(text="3 Mon - 250 ⭐️ (-17%)", callback_data="premium_3_months"))
    b.row(InlineKeyboardButton(text="1 Year - 800 ⭐️ (-33%)", callback_data="premium_1_year"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await c.message.edit_text(safe_format_text(get_text(lang, "premium_description")), reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_premium_1_month(c):
    await c.message.answer_invoice("Premium (1 mon)", "30 days", "premium_30_days", "", "XTR", [LabeledPrice(label="1", amount=100)])
    await c.answer()
async def handle_premium_3_months(c):
    await c.message.answer_invoice("Premium (3 mon)", "90 days", "premium_90_days", "", "XTR", [LabeledPrice(label="3", amount=250)])
    await c.answer()
async def handle_premium_1_year(c):
    await c.message.answer_invoice("Premium (1 year)", "365 days", "premium_365_days", "", "XTR", [LabeledPrice(label="1", amount=800)])
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
    await m.answer(f"🌟 Success!")

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