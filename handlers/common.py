import logging
import asyncio # <--- ДОБАВЛЕН ЭТОТ ВАЖНЫЙ ИМПОРТ
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
    # Получаем актуальный язык из БД, иначе английский
    lang = user_data.get('language_code', 'en') 
    is_premium = user_data.get('is_premium', False)
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(first_name)))
    
    # Отправляем БЕЗ клавиатуры (Clean Flow), так как кнопки теперь только по вызову
    await message.answer(welcome_text, parse_mode="HTML")
    
    await track_safely(user_id, "start_command", {"language": lang})
    
    # Подарок
    if user_data.get('trial_status') == 'pending':
        created_at = user_data.get('created_at')
        if created_at:
            now = datetime.now(created_at.tzinfo)
            if (now - created_at).total_seconds() < 120:
                await asyncio.sleep(2)
                gift_text = safe_format_text(get_text(lang, "welcome_gift_alert"))
                await message.answer(gift_text, parse_mode="HTML")

# --- RESTART ---
async def handle_restart(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    is_premium = user_data.get('is_premium', False)
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(callback.from_user.first_name)))
    # Здесь показываем кнопки только при явном вызове меню, если хотите.
    # Но в текущем дизайне мы решили убирать кнопки при старте.
    # Если нажата кнопка "Назад" (main_menu), логично увидеть меню.
    # Если вы хотите меню по кнопке "Назад" - раскомментируйте kb ниже и вставьте в edit_text
    
    # kb = get_main_menu_keyboard(lang, is_premium)
    
    try: await callback.message.edit_text(welcome_text, reply_markup=None, parse_mode="HTML")
    except: await callback.message.answer(welcome_text, reply_markup=None, parse_mode="HTML")
    await callback.answer()

async def handle_main_menu(callback: CallbackQuery):
    # А вот кнопка "Назад" должна возвращать КЛАВИАТУРУ МЕНЮ, иначе как пользоваться?
    # Исправим логику для handle_main_menu: она должна возвращать кнопки!
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    is_premium = user_data.get('is_premium', False)
    
    kb = get_main_menu_keyboard(lang, is_premium)
    txt = safe_format_text(get_text(lang, "menu")) # Используем текст "Главное меню"
    
    try: await callback.message.edit_text(txt, reply_markup=kb, parse_mode="HTML")
    except: await callback.message.answer(txt, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

async def cmd_favorites(m):
    uid = m.from_user.id
    user_data = await users_repo.get_user(uid)
    # Используем язык из БД!
    lang = user_data.get('language_code', 'en')
    favs, p = await favorites_repo.get_favorites_page(uid, 1)
    if not favs:
        await m.answer(get_text(lang, "favorites_empty"))
        return
    h = safe_format_text(get_text(lang, "favorites_title")) + f" (1/{p})"
    b = InlineKeyboardBuilder()
    for f in favs:
        date_str = f['created_at'].strftime('%d.%m') if f.get('created_at') else ""
        b.row(InlineKeyboardButton(text=f"{f['dish_name']} ({date_str})", callback_data=f"view_fav_{f['id']}"))
    if p>1: b.row(InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(h, reply_markup=b.as_markup(), parse_mode="HTML")
    await track_safely(uid, "favorites_viewed", {"page": 1})

async def handle_show_favorites(c):
    from handlers.favorites import handle_favorite_pagination
    c.data = "fav_page_1"
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

async def handle_set_language(c: CallbackQuery):
    l = c.data.split("_")[2]
    await users_repo.update_language(c.from_user.id, l)
    
    # Сразу показываем меню на новом языке
    # Чтобы юзер видел, что язык сменился
    user_data = await users_repo.get_user(c.from_user.id)
    kb = get_main_menu_keyboard(l, user_data.get('is_premium', False))
    txt = safe_format_text(get_text(l, "menu")) # "Main Menu" on new lang
    
    await c.message.edit_text(txt, reply_markup=kb, parse_mode="HTML")
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
    await track_safely(uid, "help_viewed", {"language": lang})

async def handle_show_help(c): await cmd_help(c.message)

async def cmd_stats(m):
    uid = m.from_user.id
    st = await users_repo.get_usage_stats(uid)
    if not st: return
    user_data = await users_repo.get_user(uid)
    lang = user_data.get('language_code', 'en')
    s = "💎 PREMIUM" if st['is_premium'] else "👤 FREE"
    t = (f"📊 <b>Statistics</b>\n\n{s}\n📝 Text: {st['text_requests_used']}/{st['text_requests_limit']}\n"
         f"🎤 Voice: {st['voice_requests_used']}/{st['voice_requests_limit']}")
    b = InlineKeyboardBuilder()
    if not st['is_premium']: b.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(t, reply_markup=b.as_markup(), parse_mode="HTML")

async def cmd_code(m):
    uid = m.from_user.id
    user_data = await users_repo.get_user(uid)
    lang = user_data.get('language_code', 'en')
    args = m.text.split()
    if len(args)<2: 
        await m.answer(safe_format_text(get_text(lang, "promo_instruction")), parse_mode="HTML")
        return
    if args[1].strip() == SECRET_PROMO_CODE:
        if await users_repo.activate_premium(uid, 365*99):
            await m.answer("💎 Success! Premium activated.", parse_mode="HTML")
            await track_safely(uid, "premium_activated", {"method": "promo"})
    else: await m.answer("🚫 Invalid code.")

async def cmd_admin(m):
    if m.from_user.id in ADMIN_IDS: await m.answer("Admin: /stats /users /reset ID")

async def handle_noop(c): await c.answer()

async def handle_buy_premium(c: CallbackQuery):
    user_data = await users_repo.get_user(c.from_user.id)
    lang = user_data.get('language_code', 'en')
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="1 Mon - 100 ⭐️", callback_data="premium_1_month"))
    b.row(InlineKeyboardButton(text="3 Mon - 250 ⭐️ (-17%)", callback_data="premium_3_months"))
    b.row(InlineKeyboardButton(text="1 Year - 800 ⭐️ (-33%)", callback_data="premium_1_year"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await c.message.edit_text(safe_format_text(get_text(lang, "premium_description")), reply_markup=b.as_markup(), parse_mode="HTML")
    await c.answer()

async def handle_premium_1_month(c):
    await c.message.answer_invoice("Premium (1 mon)", "30 days", "premium_30_days", "", "XTR", [LabeledPrice(label="1", amount=100)])
    await c.answer()
async def handle_premium_3_months(c):
    await c.message.answer_invoice("Premium (3 mon)", "90 days", "premium_90_days", "", "XTR", [LabeledPrice(label="3", amount=250)])
    await c.answer()
async def handle_premium_1_year(c):
    await c.message.answer_invoice("Premium (1 yr)", "365 days", "premium_365_days", "", "XTR", [LabeledPrice(label="1", amount=800)])
    await c.answer()
async def on_pre_checkout_query(q): await q.answer(ok=True)
async def on_successful_payment(m):
    p = m.successful_payment.invoice_payload
    days = 30
    if "90" in p: days = 90
    elif "365" in p: days = 365
    await users_repo.activate_premium(m.from_user.id, days)
    user_data = await users_repo.get_user(m.from_user.id)
    lang = user_data.get('language_code', 'en')
    kb = get_main_menu_keyboard(lang, True)
    await m.answer(f"🌟 Success! {days} days added.", reply_markup=kb, parse_mode="HTML")

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