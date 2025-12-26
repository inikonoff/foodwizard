import logging
import re
from datetime import datetime
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import html

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

# --- START ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    user_data = await users_repo.get_or_create(user_id, first_name, username)
    lang = user_data.get('language_code', 'en')
    is_premium = user_data.get('is_premium', False)
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(first_name)))
    # ОТПРАВЛЯЕМ БЕЗ КЛАВИАТУРЫ
    await message.answer(welcome_text, parse_mode="HTML")
    
    await track_safely(user_id, "start_command", {"language": lang})
    
    if user_data.get('trial_status') == 'pending':
        created_at = user_data.get('created_at')
        if created_at:
            now = datetime.now(created_at.tzinfo)
            if (now - created_at).total_seconds() < 60:
                await asyncio.sleep(2)
                gift_text = safe_format_text(get_text(lang, "welcome_gift_alert"))
                await message.answer(gift_text, parse_mode="HTML")

# RESTART
async def handle_restart(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    is_premium = user_data.get('is_premium', False)
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(callback.from_user.first_name)))
    kb = get_main_menu_keyboard(lang, is_premium)
    try: await callback.message.edit_text(welcome_text, reply_markup=kb, parse_mode="HTML")
    except: await callback.message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

async def handle_main_menu(callback: CallbackQuery):
    await handle_restart(callback)

# --- FAVORITES ---
async def cmd_favorites(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    favorites, pages = await favorites_repo.get_favorites_page(user_id, 1)
    
    if not favorites:
        await message.answer(get_text(lang, "favorites_empty"))
        return
    
    header = safe_format_text(get_text(lang, "favorites_title")) + f" (1/{pages})"
    b = InlineKeyboardBuilder()
    for fav in favorites:
        b.row(InlineKeyboardButton(text=f"{fav['dish_name']} ({fav['created_at'].strftime('%d.%m')})", callback_data=f"view_fav_{fav['id']}"))
    if pages > 1:
        b.row(InlineKeyboardButton(text="1", callback_data="noop"), InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await message.answer(header, reply_markup=b.as_markup(), parse_mode="HTML")
    await track_safely(user_id, "favorites_viewed", {"page": 1})

async def handle_show_favorites(c):
    from handlers.favorites import handle_favorite_pagination
    c.data = "fav_page_1"
    await handle_favorite_pagination(c)

# --- LANG ---
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

async def handle_set_language(c: CallbackQuery):
    l_code = c.data.split("_")[2]
    await users_repo.update_language(c.from_user.id, l_code)
    uid = c.from_user.id
    ud = await users_repo.get_user(uid)
    w = safe_format_text(get_text(l_code, "welcome", name=html.quote(c.from_user.first_name)))
    kb = get_main_menu_keyboard(l_code, ud.get('is_premium', False))
    await c.message.edit_text(w, reply_markup=kb, parse_mode="HTML")
    await track_safely(uid, "language_changed", {"lang": l_code})
    await c.answer(get_text(l_code, "lang_changed"))

# --- HELP ---
async def cmd_help(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    t = safe_format_text(get_text(lang, 'help_title'))
    tx = safe_format_text(get_text(lang, 'help_text'))
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(f"<b>{t}</b>\n\n{tx}", reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_show_help(c): await cmd_help(c.message)

# --- ADMIN/CODE/STATS ---
async def cmd_code(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    args = m.text.split()
    if len(args)<2: 
        await m.answer("Code: <code>PROMO123</code>", parse_mode="HTML")
        return
    if args[1].strip() == SECRET_PROMO_CODE:
        if await users_repo.activate_premium(uid, 365*99):
            await m.answer("💎 Success!")
            await track_safely(uid, "premium_activated", {"method": "promo"})
    else: await m.answer("🚫 Invalid")

async def cmd_stats(m):
    uid = m.from_user.id
    st = await users_repo.get_usage_stats(uid)
    if not st: return
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    stat = "💎 PREMIUM" if st['is_premium'] else "👤 FREE"
    t = f"📊 <b>Statistics</b>\n\n{stat}\nTXT: {st['text_requests_used']}/{st['text_requests_limit']}\nVOICE: {st['voice_requests_used']}/{st['voice_requests_limit']}"
    b = InlineKeyboardBuilder()
    if not st['is_premium']: b.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(t, reply_markup=b.as_markup(), parse_mode="HTML")

async def cmd_admin(m):
    if m.from_user.id in ADMIN_IDS: await m.answer("Admin: /stats, /users, /reset ID")

async def handle_noop(c): await c.answer()

# --- ОПЛАТА (TELEGRAM STARS) ---

async def handle_buy_premium(c: CallbackQuery):
    lang = (await users_repo.get_user(c.from_user.id)).get('language_code', 'en')
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="1 Mon - 100 ⭐️", callback_data="premium_1_month"))
    b.row(InlineKeyboardButton(text="3 Mon - 250 ⭐️", callback_data="premium_3_months"))
    b.row(InlineKeyboardButton(text="1 Year - 800 ⭐️", callback_data="premium_1_year"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    desc = safe_format_text(get_text(lang, "premium_description"))
    await c.message.edit_text(desc, reply_markup=b.as_markup(), parse_mode="HTML")

async def handle_premium_1_month(c):
    await c.message.answer_invoice("Premium (1 month)", "30 days full access", "premium_30_days", "", "XTR", [LabeledPrice(label="1 month", amount=100)])
    await c.answer()

async def handle_premium_3_months(c):
    await c.message.answer_invoice("Premium (3 months)", "90 days full access", "premium_90_days", "", "XTR", [LabeledPrice(label="3 months", amount=250)])
    await c.answer()

async def handle_premium_1_year(c):
    await c.message.answer_invoice("Premium (1 year)", "365 days full access", "premium_365_days", "", "XTR", [LabeledPrice(label="1 year", amount=800)])
    await c.answer()

async def on_pre_checkout_query(q): await q.answer(ok=True)

# !!! ОБНОВЛЕННАЯ ФУНКЦИЯ УСПЕШНОЙ ОПЛАТЫ С УВЕДОМЛЕНИЕМ АДМИНОВ !!!
async def on_successful_payment(message: Message):
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload
    user_id = message.from_user.id
    
    days = 30
    if "90" in payload: days = 90
    if "365" in payload: days = 365
    
    # 1. Активация пользователю
    success = await users_repo.activate_premium(user_id, days)
    
    if success:
        lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
        kb = get_main_menu_keyboard(lang, True) # Меню для премиума (без кнопки купить)
        
        await message.answer(f"🌟 <b>Success!</b> Premium for {days} days activated.", reply_markup=kb, parse_mode="HTML")
        await track_safely(user_id, "payment_success", {"amount": payment_info.total_amount, "currency": "XTR", "days": days})

        # 2. УВЕДОМЛЕНИЕ АДМИНУ (НОВАЯ ЧАСТЬ)
        # Получаем имя для красоты
        user_name = html.quote(message.from_user.full_name)
        username = message.from_user.username
        username_text = f"(@{username})" if username else ""
        
        admin_alert = (
            f"💰 <b>НОВАЯ ПРОДАЖА!</b>\n\n"
            f"👤 <b>Пользователь:</b> {user_name} {username_text} (ID: <code>{user_id}</code>)\n"
            f"📅 <b>Тариф:</b> {days} дней\n"
            f"💸 <b>Сумма:</b> {payment_info.total_amount} XTR\n"
            f"🌍 <b>Язык:</b> {lang}"
        )
        
        # Отправляем всем админам из списка ADMIN_IDS
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(admin_id, admin_alert, parse_mode="HTML")
                logger.info(f"Админ {admin_id} уведомлен о продаже.")
            except Exception as e:
                logger.warning(f"Не удалось уведомить админа {admin_id}: {e}")
                
    else:
        logger.error(f"FATAL: Деньги списаны, но премиум не выдан! User: {user_id}, Days: {days}")
        await message.answer("⚠️ Error activating premium. Please contact support.")


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
    dp.callback_query.register(handle_restart, F.data == "restart")
    dp.callback_query.register(handle_noop, F.data == "noop")
    
    dp.callback_query.register(handle_buy_premium, F.data == "buy_premium")
    dp.callback_query.register(handle_premium_1_month, F.data == "premium_1_month")
    dp.callback_query.register(handle_premium_3_months, F.data == "premium_3_months")
    dp.callback_query.register(handle_premium_1_year, F.data == "premium_1_year")
    
    dp.pre_checkout_query.register(on_pre_checkout_query)
    dp.message.register(on_successful_payment, F.content_type == ContentType.SUCCESSFUL_PAYMENT)