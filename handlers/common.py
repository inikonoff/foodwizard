import logging
from datetime import datetime, timedelta
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
from config import SUPPORTED_LANGUAGES, ADMIN_IDS, SECRET_PROMO_CODE

logger = logging.getLogger(__name__)

# --- ŠŽŒ€„€ /START ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    # ®«ãç ¥¬ ¨«¨ á®§¤ ñ¬ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_or_create(
        user_id=user_id,
        first_name=first_name,
        username=username
    )
    
    # Ž¯à¥¤¥«ï¥¬ ï§ëª ¯®«ì§®¢ â¥«ï
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # Žâ¯à ¢«ï¥¬ ¯à¨¢¥âáâ¢¥­­®¥ á®®¡é¥­¨¥
    welcome_text = get_text(lang, "welcome", name=first_name)
    start_manual = get_text(lang, "start_manual")
    
    # ‘®§¤ ñ¬ ª« ¢¨ âãàã á ®á­®¢­ë¬¨ ª®¬ ­¤ ¬¨
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_favorites"),
            callback_data="show_favorites"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_change_lang"),
            callback_data="change_language"
        ),
        InlineKeyboardButton(
            text=get_text(lang, "btn_help"),
            callback_data="show_help"
        )
    )
    
    full_text = f"{welcome_text}\n\n{start_manual}"
    await message.answer(full_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    # ‹®£¨àã¥¬ á®¡ëâ¨¥
    await metrics.track_event(user_id, "start_command", {"language": lang})

# --- ŠŽŒ€„€ /FAVORITES ---
async def cmd_favorites(message: Message):
    user_id = message.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ®«ãç ¥¬ ¯¥à¢ãî áâà ­¨æã ¨§¡à ­­®£®
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page=1)
    
    if not favorites:
        await message.answer(get_text(lang, "favorites_empty"))
        return
    
    # ”®à¬ â¨àã¥¬ á¯¨á®ª à¥æ¥¯â®¢
    recipes_text = ""
    for i, fav in enumerate(favorites, 1):
        date_str = fav['created_at'].strftime("%d.%m.%Y")
        recipes_text += get_text(lang, "favorites_recipe_item", 
                               num=i, dish=fav['dish_name'], date=date_str)
    
    # ‘®§¤ ñ¬ ª« ¢¨ âãàã á ¯ £¨­ æ¨¥©
    builder = InlineKeyboardBuilder()
    
    # Š­®¯ª¨ ¯ £¨­ æ¨¨
    if total_pages > 1:
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_prev"),
                callback_data=f"fav_page_1"
            ),
            InlineKeyboardButton(
                text=f"1/{total_pages}",
                callback_data="noop"
            ),
            InlineKeyboardButton(
                text=get_text(lang, "btn_next"),
                callback_data=f"fav_page_2"
            )
        )
    
    # Š­®¯ª  ¢®§¢à â 
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    # Žâ¯à ¢«ï¥¬ á®®¡é¥­¨¥
    text = get_text(lang, "favorites_list", page=1, total_pages=total_pages, recipes=recipes_text)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    # ‹®£¨àã¥¬ á®¡ëâ¨¥
    await metrics.track_event(user_id, "favorites_viewed", {"page": 1, "total": len(favorites)})

# --- ŠŽŒ€„€ /LANG ---
async def cmd_lang(message: Message):
    user_id = message.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    current_lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ‘®§¤ ñ¬ ª« ¢¨ âãàã ¢ë¡®à  ï§ëª 
    builder = InlineKeyboardBuilder()
    
    # „®¡ ¢«ï¥¬ ª­®¯ª¨ ¤«ï ¢á¥å ¯®¤¤¥à¦¨¢ ¥¬ëå ï§ëª®¢
    for lang_code in SUPPORTED_LANGUAGES:
        builder.row(
            InlineKeyboardButton(
                text=get_text(current_lang, f"lang_{lang_code}"),
                callback_data=f"set_lang_{lang_code}"
            )
        )
    
    # „®¡ ¢«ï¥¬ ª­®¯ªã ®â¬¥­ë
    builder.row(
        InlineKeyboardButton(
            text=get_text(current_lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    await message.answer(
        get_text(current_lang, "choose_language"),
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# --- ŠŽŒ€„€ /HELP ---
async def cmd_help(message: Message):
    user_id = message.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    help_text = f"{get_text(lang, 'help_title')}\n{get_text(lang, 'help_text')}"
    
    # ‘®§¤ ñ¬ ª« ¢¨ âãàã
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    await message.answer(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    # ‹®£¨àã¥¬ á®¡ëâ¨¥
    await metrics.track_event(user_id, "help_viewed", {"language": lang})

# --- ŠŽŒ€„€ /CODE ---
async def cmd_code(message: Message):
    """€ªâ¨¢ æ¨ï ¯à¥¬¨ã¬  ¯® ¯à®¬®ª®¤ã"""
    user_id = message.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # à®¢¥àï¥¬  à£ã¬¥­âë
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "‚¢¥¤¨â¥ ª®¤. à¨¬¥à:\n"
            f"<code>/code {SECRET_PROMO_CODE}</code>",
            parse_mode="HTML"
        )
        return
    
    code = args[1].strip()
    
    if code == SECRET_PROMO_CODE:
        # €ªâ¨¢¨àã¥¬ ¯à¥¬¨ã¬ ­  99 «¥â (èãâª )
        success = await users_repo.activate_premium(user_id, days=365*99)
        
        if success:
            response = (
                "?? <b>Š®¤ ¯à¨­ïâ!</b>\n\n"
                "€ªâ¨¢¨à®¢ ­ ¢à¥¬¥­­ë© ¤®áâã¯ ª ¯à¥¬¨ã¬ äã­ªæ¨ï¬ ­  <b>99 «¥â</b>.\n"
                "® ¨áâ¥ç¥­¨¨ áà®ª  ¤¥©áâ¢¨ï ­¥ § ¡ã¤ìâ¥ ¯à®¤«¨âì ¯®¤¯¨áªã. ??"
            )
            await message.answer(response, parse_mode="HTML")
            
            # ‹®£¨àã¥¬  ªâ¨¢ æ¨î ¯à¥¬¨ã¬ 
            await metrics.track_event(user_id, "premium_activated", {
                "method": "promo_code",
                "days": 365*99
            })
        else:
            await message.answer("? Žè¨¡ª   ªâ¨¢ æ¨¨ ¯à¥¬¨ã¬ ")
    else:
        await message.answer("? ¥¢¥à­ë© ª®¤.")

# --- ŠŽŒ€„€ /STATS ---
async def cmd_stats(message: Message):
    """®ª §ë¢ ¥â áâ â¨áâ¨ªã ¨á¯®«ì§®¢ ­¨ï"""
    user_id = message.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ®«ãç ¥¬ áâ â¨áâ¨ªã ¨á¯®«ì§®¢ ­¨ï
    usage_stats = await users_repo.get_usage_stats(user_id)
    
    if not usage_stats:
        await message.answer("‘â â¨áâ¨ª  ­¥¤®áâã¯­ ")
        return
    
    # ”®à¬¨àã¥¬ á®®¡é¥­¨¥
    status = "?? …Œˆ“Œ" if usage_stats['is_premium'] else "?? …‘‹€’Ž"
    
    if usage_stats['premium_until']:
        premium_until = usage_stats['premium_until'].strftime("%d.%m.%Y")
        status += f" (¤® {premium_until})"
    
    stats_text = (
        f"?? <b>‚ è  áâ â¨áâ¨ª </b>\n\n"
        f"{status}\n\n"
        f"?? <b>’¥ªáâ®¢ë¥ § ¯à®áë:</b>\n"
        f"   ˆá¯®«ì§®¢ ­®: {usage_stats['text_requests_used']}/{usage_stats['text_requests_limit']}\n"
        f"   Žáâ «®áì: {usage_stats['remaining_text']}\n\n"
        f"?? <b>ƒ®«®á®¢ë¥ § ¯à®áë:</b>\n"
        f"   ˆá¯®«ì§®¢ ­®: {usage_stats['voice_requests_used']}/{usage_stats['voice_requests_limit']}\n"
        f"   Žáâ «®áì: {usage_stats['remaining_voice']}\n\n"
        f"?? <b>‚á¥£® § ¯à®á®¢:</b> {usage_stats['total_requests']}\n"
        f"?? <b>‘¡à®á «¨¬¨â®¢:</b> {usage_stats['last_reset_date'].strftime('%d.%m.%Y')}"
    )
    
    # ‘®§¤ ñ¬ ª« ¢¨ âãàã
    builder = InlineKeyboardBuilder()
    
    if not usage_stats['is_premium']:
        builder.row(
            InlineKeyboardButton(
                text="?? Šã¯¨âì ¯à¥¬¨ã¬",
                callback_data="buy_premium"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    await message.answer(stats_text, reply_markup=builder.as_markup(), parse_mode="HTML")

# --- ŠŽŒ€„€ /ADMIN ---
async def cmd_admin(message: Message):
    """€¤¬¨­-ª®¬ ­¤ë (â®«ìª® ¤«ï ADMIN_IDS)"""
    user_id = message.from_user.id
    
    # à®¢¥àï¥¬ ¯à ¢ 
    if user_id not in ADMIN_IDS:
        await message.answer("? „®áâã¯ § ¯à¥éñ­")
        return
    
    #  àá¨¬  à£ã¬¥­âë
    args = message.text.split()
    
    if len(args) < 2:
        # ®ª §ë¢ ¥¬ á¯¨á®ª ª®¬ ­¤
        help_text = (
            "?? <b>€¤¬¨­-¯ ­¥«ì</b>\n\n"
            "<b>Š®¬ ­¤ë:</b>\n"
            "/admin stats - ®¡é ï áâ â¨áâ¨ª \n"
            "/admin premium [user_id] - ¢ë¤ âì ¯à¥¬¨ã¬\n"
            "/admin users [N] - á¯¨á®ª ¯®«ì§®¢ â¥«¥©\n"
            "/admin reset [user_id] - á¡à®á¨âì «¨¬¨âë\n"
            "/admin broadcast - à ááë«ª \n"
        )
        await message.answer(help_text, parse_mode="HTML")
        return
    
    command = args[1].lower()
    
    if command == "stats":
        # Ž¡é ï áâ â¨áâ¨ª 
        total_users = await users_repo.count_users()
        expired = await users_repo.check_premium_expiry()
        
        stats = (
            f"?? <b>Ž¡é ï áâ â¨áâ¨ª </b>\n\n"
            f"?? ‚á¥£® ¯®«ì§®¢ â¥«¥©: {total_users}\n"
            f"?? „¥ ªâ¨¢¨à®¢ ­® ¯à¥¬¨ã¬®¢: {expired}\n"
            # ‡¤¥áì ¬®¦­® ¤®¡ ¢¨âì áâ â¨áâ¨ªã ¨§ metrics
        )
        await message.answer(stats, parse_mode="HTML")
    
    elif command == "premium" and len(args) >= 3:
        # ‚ë¤ ç  ¯à¥¬¨ã¬ 
        try:
            target_user_id = int(args[2])
            days = int(args[3]) if len(args) >= 4 else 30
            
            success = await users_repo.activate_premium(target_user_id, days)
            
            if success:
                await message.answer(f"? à¥¬¨ã¬ ¢ë¤ ­ ¯®«ì§®¢ â¥«î {target_user_id} ­  {days} ¤­¥©")
            else:
                await message.answer(f"? Žè¨¡ª  ¢ë¤ ç¨ ¯à¥¬¨ã¬ ")
        except ValueError:
            await message.answer("? ¥¢¥à­ë© ä®à¬ â ID ¯®«ì§®¢ â¥«ï")
    
    elif command == "users":
        # ‘¯¨á®ª ¯®«ì§®¢ â¥«¥©
        limit = int(args[2]) if len(args) >= 3 else 10
        
        users = await users_repo.get_all_users(limit)
        
        if not users:
            await message.answer("¥â ¯®«ì§®¢ â¥«¥©")
            return
        
        users_text = "?? <b>®á«¥¤­¨¥ ¯®«ì§®¢ â¥«¨:</b>\n\n"
        for i, user in enumerate(users, 1):
            premium = "??" if user['is_premium'] else "??"
            users_text += f"{i}. {user['first_name']} ({user['user_id']}) {premium}\n"
        
        await message.answer(users_text, parse_mode="HTML")
    
    elif command == "reset" and len(args) >= 3:
        # ‘¡à®á «¨¬¨â®¢ ¯®«ì§®¢ â¥«ï
        try:
            target_user_id = int(args[2])
            
            # Ž¡­ã«ï¥¬ áç¥âç¨ª¨
            async with db.connection() as conn:
                await conn.execute(
                    """
                    UPDATE users 
                    SET requests_today = 0, 
                        voice_requests_today = 0,
                        last_reset_date = CURRENT_DATE
                    WHERE user_id = $1
                    """,
                    target_user_id
                )
            
            await message.answer(f"? ‹¨¬¨âë ¯®«ì§®¢ â¥«ï {target_user_id} á¡à®è¥­ë")
        except ValueError:
            await message.answer("? ¥¢¥à­ë© ä®à¬ â ID ¯®«ì§®¢ â¥«ï")
    
    elif command == "broadcast":
        #  ááë«ª  (ã¯à®éñ­­ ï ¢¥àá¨ï)
        if len(args) < 3:
            await message.answer("ˆá¯®«ì§®¢ ­¨¥: /admin broadcast [á®®¡é¥­¨¥]")
            return
        
        broadcast_text = " ".join(args[2:])
        users = await users_repo.get_all_users(1000)
        
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
                await message.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"?? <b>Ž¡êï¢«¥­¨¥ ®â  ¤¬¨­¨áâà â®à :</b>\n\n{broadcast_text}",
                    parse_mode="HTML"
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Žè¨¡ª  ®â¯à ¢ª¨ à ááë«ª¨ ¯®«ì§®¢ â¥«î {user['user_id']}: {e}")
                fail_count += 1
        
        await message.answer(
            f"?  ááë«ª  § ¢¥àè¥­ :\n"
            f"? “á¯¥è­®: {success_count}\n"
            f"? Žè¨¡®ª: {fail_count}"
        )

# --- ŠŽ‹‹Šˆ ---
async def handle_change_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    current_lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ‘®§¤ ñ¬ ª« ¢¨ âãàã ¢ë¡®à  ï§ëª 
    builder = InlineKeyboardBuilder()
    
    for lang_code in SUPPORTED_LANGUAGES:
        builder.row(
            InlineKeyboardButton(
                text=get_text(current_lang, f"lang_{lang_code}"),
                callback_data=f"set_lang_{lang_code}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text=get_text(current_lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    await callback.message.edit_text(
        get_text(current_lang, "choose_language"),
        reply_markup=builder.as_markup()
    )
    await callback.answer()

async def handle_set_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[2]  # set_lang_ru -> ru
    
    # Ž¡­®¢«ï¥¬ ï§ëª ¯®«ì§®¢ â¥«ï
    await users_repo.update_language(user_id, lang_code)
    
    # ®«ãç ¥¬ ¨¬ï ¯®«ì§®¢ â¥«ï ¤«ï ¯à¨¢¥âáâ¢¨ï
    user_data = await users_repo.get_user(user_id)
    first_name = user_data.get('first_name', 'User') if user_data else 'User'
    
    # Žâ¯à ¢«ï¥¬ ¯®¤â¢¥à¦¤¥­¨¥
    welcome_text = get_text(lang_code, "welcome", name=first_name)
    start_manual = get_text(lang_code, "start_manual")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang_code, "btn_favorites"),
            callback_data="show_favorites"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang_code, "btn_change_lang"),
            callback_data="change_language"
        ),
        InlineKeyboardButton(
            text=get_text(lang_code, "btn_help"),
            callback_data="show_help"
        )
    )
    
    full_text = f"{welcome_text}\n\n{start_manual}"
    await callback.message.edit_text(
        full_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    
    # ‹®£¨àã¥¬ á¬¥­ã ï§ëª 
    await metrics.track_event(user_id, "language_changed", {"language": lang_code})
    await callback.answer(get_text(lang_code, "lang_changed"))

async def handle_show_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ®«ãç ¥¬ ¯¥à¢ãî áâà ­¨æã ¨§¡à ­­®£®
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page=1)
    
    if not favorites:
        await callback.message.edit_text(get_text(lang, "favorites_empty"))
        await callback.answer()
        return
    
    # ”®à¬ â¨àã¥¬ á¯¨á®ª
    recipes_text = ""
    for i, fav in enumerate(favorites, 1):
        date_str = fav['created_at'].strftime("%d.%m.%Y")
        recipes_text += get_text(lang, "favorites_recipe_item", 
                               num=i, dish=fav['dish_name'], date=date_str)
    
    # ‘®§¤ ñ¬ ª« ¢¨ âãàã
    builder = InlineKeyboardBuilder()
    
    if total_pages > 1:
        builder.row(
            InlineKeyboardButton(
                text=get_text(lang, "btn_prev"),
                callback_data=f"fav_page_1"
            ),
            InlineKeyboardButton(
                text=f"1/{total_pages}",
                callback_data="noop"
            ),
            InlineKeyboardButton(
                text=get_text(lang, "btn_next"),
                callback_data=f"fav_page_2"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    text = get_text(lang, "favorites_list", page=1, total_pages=total_pages, recipes=recipes_text)
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

async def handle_show_help(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    help_text = f"{get_text(lang, 'help_title')}\n{get_text(lang, 'help_text')}"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_back"),
            callback_data="main_menu"
        )
    )
    
    await callback.message.edit_text(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

async def handle_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    first_name = user_data.get('first_name', 'User') if user_data else 'User'
    
    welcome_text = get_text(lang, "welcome", name=first_name)
    start_manual = get_text(lang, "start_manual")
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_favorites"),
            callback_data="show_favorites"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text(lang, "btn_change_lang"),
            callback_data="change_language"
        ),
        InlineKeyboardButton(
            text=get_text(lang, "btn_help"),
            callback_data="show_help"
        )
    )
    
    full_text = f"{welcome_text}\n\n{start_manual}"
    await callback.message.edit_text(
        full_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

async def handle_noop(callback: CallbackQuery):
    """ãáâ®© ®¡à ¡®âç¨ª ¤«ï ª­®¯®ª-§ £«ãè¥ª"""
    await callback.answer()

async def handle_buy_premium(callback: CallbackQuery):
    """Ž¡à ¡®âç¨ª ª­®¯ª¨ ¯®ªã¯ª¨ ¯à¥¬¨ã¬ """
    user_id = callback.from_user.id
    
    # ®«ãç ¥¬ ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    # ‘®§¤ ñ¬ ª« ¢¨ âãàã á ¢ à¨ ­â ¬¨ ¯®¤¯¨áª¨
    builder = InlineKeyboardBuilder()
    
    # Š­®¯ª¨ ¤«ï ¯®ªã¯ª¨ ç¥à¥§ Telegram Stars
    builder.row(
        InlineKeyboardButton(
            text="1 ¬¥áïæ - 100 §¢ñ§¤ ?",
            callback_data="premium_1_month"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="3 ¬¥áïæ  - 250 §¢ñ§¤ ? (íª®­®¬¨ï 17%)",
            callback_data="premium_3_months"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="1 £®¤ - 800 §¢ñ§¤ ? (íª®­®¬¨ï 33%)",
            callback_data="premium_1_year"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="?? ‚¥à­ãâìáï",
            callback_data="main_menu"
        )
    )
    
    text = (
        "?? <b>à¥¬¨ã¬ ¯®¤¯¨áª </b>\n\n"
        "? <b>—â® ¢å®¤¨â:</b>\n"
        " 100 â¥ªáâ®¢ëå § ¯à®á®¢ ¢ ¤¥­ì\n"
        " 50 £®«®á®¢ëå § ¯à®á®¢ ¢ ¤¥­ì\n"
        " à¨®à¨â¥â­ ï ®¡à ¡®âª \n"
        " „®áâã¯ ª ­®¢ë¬ äã­ªæ¨ï¬ ¯¥à¢ë¬\n"
        " ®¤¤¥à¦ª  à §à ¡®âç¨ª  ??\n\n"
        "?? <b>‹¨¬¨âë ®¡­®¢«ïîâáï ª ¦¤ë© ¤¥­ì ¢ 00:00</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

# --- Ž€Ž’—ˆŠˆ ‚›Ž€ Ž„ˆ‘Šˆ ---
async def handle_premium_1_month(callback: CallbackQuery):
    await callback.answer("?? â  äã­ªæ¨ï áª®à® ¡ã¤¥â ¤®áâã¯­ !")
    # ‡¤¥áì ¡ã¤¥â ¨­â¥£à æ¨ï á Telegram Payments

async def handle_premium_3_months(callback: CallbackQuery):
    await callback.answer("?? â  äã­ªæ¨ï áª®à® ¡ã¤¥â ¤®áâã¯­ !")

async def handle_premium_1_year(callback: CallbackQuery):
    await callback.answer("?? â  äã­ªæ¨ï áª®à® ¡ã¤¥â ¤®áâã¯­ !")

# --- …ƒˆ‘’€–ˆŸ Ž€Ž’—ˆŠŽ‚ ---
def register_common_handlers(dp: Dispatcher):
    # Š®¬ ­¤ë
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_favorites, Command("favorites"))
    dp.message.register(cmd_lang, Command("lang"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_code, Command("code"))
    dp.message.register(cmd_stats, Command("stats"))
    dp.message.register(cmd_admin, Command("admin"))
    
    # Š®««¡íª¨
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
