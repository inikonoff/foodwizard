import logging
from datetime import datetime, timedelta
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db # Оставлено для команды /admin reset
from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
from config import SUPPORTED_LANGUAGES, ADMIN_IDS, SECRET_PROMO_CODE

logger = logging.getLogger(__name__)

# --- Вспомогательная функция для безопасного логирования метрик ---
async def track_safely(user_id: int, event_name: str, data: dict = None):
    try:
        await metrics.track_event(user_id, event_name, data)
    except Exception as e:
        logger.error(f"❌ Ошибка записи метрики ({event_name}): {e}", exc_info=True)


# --- КОМАНДА /START ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    # Получаем или создаём пользователя
    user_data = await users_repo.get_or_create(
        user_id=user_id,
        first_name=first_name,
        username=username
    )
    
    # Определяем язык пользователя
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Отправляем приветственное сообщение
    welcome_text = get_text(lang, "welcome", name=first_name)
    start_manual = get_text(lang, "start_manual")
    
    # Создаём клавиатуру с основными командами (опущен для краткости)
    # ... (код клавиатуры) ...
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_favorites"), callback_data="show_favorites"))
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_change_lang"), callback_data="change_language"),
                InlineKeyboardButton(text=get_text(lang, "btn_help"), callback_data="show_help"))
    
    full_text = f"{welcome_text}\n\n{start_manual}"
    await message.answer(full_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    # Логируем событие (ЗАЩИЩЕНО)
    await track_safely(user_id, "start_command", {"language": lang})

# --- КОМАНДА /FAVORITES ---
async def cmd_favorites(message: Message):
    user_id = message.from_user.id
    
    # ... (код получения данных пользователя, избранного) ...
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page=1)
    
    if not favorites:
        await message.answer(get_text(lang, "favorites_empty"))
        return
    
    # ... (код форматирования и отправки) ...
    recipes_text = ""
    for i, fav in enumerate(favorites, 1):
        date_str = fav['created_at'].strftime("%d.%m.%Y")
        recipes_text += get_text(lang, "favorites_recipe_item", num=i, dish=fav['dish_name'], date=date_str)
    
    builder = InlineKeyboardBuilder()
    # ... (код кнопок) ...
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    text = get_text(lang, "favorites_list", page=1, total_pages=total_pages, recipes=recipes_text)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    # Логируем событие (ЗАЩИЩЕНО)
    await track_safely(user_id, "favorites_viewed", {"page": 1, "total": len(favorites)})

# --- КОМАНДА /LANG --- (без изменений)

# --- КОМАНДА /HELP ---
async def cmd_help(message: Message):
    user_id = message.from_user.id
    
    # ... (код получения данных пользователя) ...
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    help_text = f"{get_text(lang, 'help_title')}\n{get_text(lang, 'help_text')}"
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    await message.answer(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    # Логируем событие (ЗАЩИЩЕНО)
    await track_safely(user_id, "help_viewed", {"language": lang})

# --- КОМАНДА /CODE ---
async def cmd_code(message: Message):
    user_id = message.from_user.id
    
    # ... (код обработки) ...
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    args = message.text.split()
    if len(args) < 2:
        # ... (ответ) ...
        return
    
    code = args[1].strip()
    
    if code == SECRET_PROMO_CODE:
        success = await users_repo.activate_premium(user_id, days=365*99)
        
        if success:
            response = (
                "?? <b>Код принят!</b>\n\n"
                "Активирован временный доступ к премиум функциям на <b>99 лет</b>.\n"
                "По истечении срока действия не забудьте продлить подписку. ??"
            )
            await message.answer(response, parse_mode="HTML")
            
            # Логируем активацию премиума (ЗАЩИЩЕНО)
            await track_safely(user_id, "premium_activated", {
                "method": "promo_code",
                "days": 365*99
            })
        else:
            await message.answer("? Ошибка активации премиума")
    else:
        await message.answer("? Неверный код.")

# --- КОМАНДА /STATS --- (без изменений)

# --- КОМАНДА /ADMIN --- (без изменений)

# --- КОЛЛБЭКИ ---
# handle_change_language, handle_show_favorites, handle_show_help, handle_main_menu, handle_noop, handle_buy_premium, handle_premium_1_month, handle_premium_3_months, handle_premium_1_year (без изменений в логике метрик)

async def handle_set_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[2]
    
    # Обновляем язык пользователя
    await users_repo.update_language(user_id, lang_code)
    
    # ... (код получения обновленных данных и клавиатуры) ...
    user_data = await users_repo.get_user(user_id)
    final_lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    final_lang = final_lang if final_lang in SUPPORTED_LANGUAGES else 'ru'

    first_name = user_data.get('first_name', 'User') if user_data else 'User'
    
    welcome_text = get_text(final_lang, "welcome", name=first_name)
    start_manual = get_text(final_lang, "start_manual")
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=get_text(final_lang, "btn_favorites"), callback_data="show_favorites"))
    builder.row(InlineKeyboardButton(text=get_text(final_lang, "btn_change_lang"), callback_data="change_language"),
                InlineKeyboardButton(text=get_text(final_lang, "btn_help"), callback_data="show_help"))
    
    full_text = f"{welcome_text}\n\n{start_manual}"
    await callback.message.edit_text(
        full_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    
    # Логируем смену языка (ЗАЩИЩЕНО)
    await track_safely(user_id, "language_changed", {"language": lang_code})
    await callback.answer(get_text(final_lang, "lang_changed"))

# ... (Остальные коллбэки без метрик) ...

def register_common_handlers(dp: Dispatcher):
    # ... (код регистрации) ...
    pass
