import logging
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
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

def get_main_menu_keyboard(lang: str, is_premium: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_favorites"), callback_data="show_favorites"))
    if not is_premium:
        builder.row(InlineKeyboardButton(text=get_text(lang, "btn_buy_premium"), callback_data="buy_premium"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_change_lang"), callback_data="change_language"),
                InlineKeyboardButton(text=get_text(lang, "btn_help"), callback_data="show_help"))
    return builder.as_markup()

async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_or_create(user_id, message.from_user.first_name, message.from_user.username)
    lang = user_data.get('language_code', 'ru')
    
    welcome = get_text(lang, "welcome", name=message.from_user.first_name).replace("**", "")
    kb = get_main_menu_keyboard(lang, user_data.get('is_premium', False))
    await message.answer(welcome, reply_markup=kb, parse_mode="HTML")
    
    # ЛОГИКА ПОДАРКА (NEW)
    if user_data.get('trial_status') == 'pending':
        created = user_data.get('created_at')
        if created:
            now = datetime.now(created.tzinfo)
            if (now - created).total_seconds() < 60:
                await message.answer(get_text(lang, "welcome_gift_alert"), parse_mode="Markdown")

# ... (Остальные функции help, lang, stats, admin - остаются как были, они рабочие) ...
# Я привожу только изменения, но для полной замены файла могу повторить весь код, если нужно.

# ... (код оплаты Stars без изменений) ...

def register_common_handlers(dp: Dispatcher):
    # ... (регистрация всех команд) ...
    dp.message.register(cmd_start, Command("start"))
    # ...