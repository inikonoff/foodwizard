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

# --- START (ИСПРАВЛЕНО: БЕЗ КНОПОК) ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    user_data = await users_repo.get_or_create(user_id, first_name, username)
    lang = user_data.get('language_code', 'en')
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(first_name)))
    
    # ОТПРАВЛЯЕМ БЕЗ КЛАВИАТУРЫ
    await message.answer(welcome_text, parse_mode="HTML")
    
    await track_safely(user_id, "start_command", {"language": lang})
    
    # Проверка на подарок
    if user_data.get('trial_status') == 'pending':
        created_at = user_data.get('created_at')
        if created_at:
            now = datetime.now(created_at.tzinfo)
            if (now - created_at).total_seconds() < 60:
                await asyncio.sleep(2)
                gift_text = safe_format_text(get_text(lang, "welcome_gift_alert"))
                await message.answer(gift_text, parse_mode="HTML")

# RESTART (Здесь кнопки НУЖНЫ, так как пользователь нажал кнопку)
async def handle_restart(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(callback.from_user.first_name)))
    kb = get_main_menu_keyboard(lang, user_data.get('is_premium', False))
    
    await callback.message.edit_text(welcome_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# --- ОСТАЛЬНОЕ БЕЗ ИЗМЕНЕНИЙ (сохраните существующий код для Favorites, Lang, Help, Code и т.д.) ---
# Чтобы код не обрывался, я скопирую сокращенные версии основных функций для связности:

async def cmd_favorites(message: Message):
    # ... см. предыдущие версии common.py
    # Важно вызвать favorites_repo.get_favorites_page и отправить ответ
    # Если хотите полный код - возьмите предыдущую версию и удалите клавиатуру ТОЛЬКО из cmd_start.
    user_id = message.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    favorites, pages = await favorites_repo.get_favorites_page(user_id, 1)
    if not favorites:
        await message.answer(get_text(lang, "favorites_empty"))
        return
    header = safe_format_text(get_text(lang, "favorites_title")) + f" (1/{pages})"
    b = InlineKeyboardBuilder()
    for fav in favorites:
        b.row(InlineKeyboardButton(text=f"{fav['dish_name']}", callback_data=f"view_fav_{fav['id']}"))
    if pages > 1: b.row(InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await message.answer(header, reply_markup=b.as_markup(), parse_mode="HTML")

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

async def cmd_help(m):
    uid = m.from_user.id
    lang = (await users_repo.get_user(uid)).get('language_code', 'en')
    t = safe_format_text(get_text(lang, 'help_title'))
    tx = safe_format_text(get_text(lang, 'help_text'))
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    await m.answer(f"<b>{t}</b>\n\n{tx}", reply_markup=b.as_markup(), parse_mode="HTML")

# ... admin, stats, code, callbacks (handle_change_language, handle_set_language, handle_buy_premium...) - все оставляем как было

async def handle_main_menu(c):
    # В Callback main menu кнопки нужны
    user_id = c.from_user.id
    ud = await users_repo.get_user(user_id)
    lang = ud.get('language_code', 'en')
    w = safe_format_text(get_text(lang, "welcome", name=html.quote(c.from_user.first_name)))
    kb = get_main_menu_keyboard(lang, ud.get('is_premium', False))
    await c.message.edit_text(w, reply_markup=kb, parse_mode="HTML")

# Обязательно сохраняйте регистрацию!
def register_common_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_favorites, Command("favorites"))
    dp.message.register(cmd_lang, Command("lang"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_code, Command("code"))
    dp.message.register(cmd_stats, Command("stats"))
    dp.message.register(cmd_admin, Command("admin"))
    
    dp.callback_query.register(handle_restart, F.data == "restart")
    dp.callback_query.register(handle_show_favorites, F.data == "show_favorites")
    # ... остальные callback регистрации ...
    # Убедитесь, что register_common_handlers в вашем файле полон (со всеми импортами и коллбэками из предыдущих версий)