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

# --- START (ТЕПЕРЬ БЕЗ КНОПОК) ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    user_data = await users_repo.get_or_create(user_id, first_name, username)
    lang = user_data.get('language_code', 'en')
    
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(first_name)))
    
    # ОТПРАВЛЯЕМ БЕЗ reply_markup!
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

# --- Остальные функции (Restart, Lang, Help, Code...) без изменений ---
# ... (Копируйте их из предыдущих ответов, там все корректно) ...

# Я приведу register для полноты картины:
async def handle_restart(callback: CallbackQuery):
    # А вот для РЕСТАРТА кнопки нужны, это логично (он ведь нажал кнопку, хочет меню)
    user_id = callback.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    welcome_text = safe_format_text(get_text(lang, "welcome", name=html.quote(callback.from_user.first_name)))
    kb = get_main_menu_keyboard(lang, user_data.get('is_premium', False))
    await callback.message.edit_text(welcome_text, reply_markup=kb, parse_mode="HTML")

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

# ... (Остальной код хендлеров: favorites, help, code, admin и callback-и. Оставляем как в последней рабочей версии common.py)

# ВАЖНО: В cmd_favorites, cmd_stats и других функциях вы можете оставить 
# get_main_menu_keyboard() или логику возврата "btn_back".

def register_common_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    # ... остальные ...
    dp.callback_query.register(handle_restart, F.data == "restart")
    # ... остальные ...
    # (Все остальные регистрации как и были)
    
    # Для сокращения я не дублирую 300 строк кода, который работает.
    # Главное изменение здесь - cmd_start без клавиатуры.