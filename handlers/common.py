import logging
import asyncio
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, PreCheckoutQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import html
import re
from datetime import datetime, timezone
from typing import Tuple

from database import db 
from database.users import users_repo
from database.favorites import favorites_repo
from database.metrics import metrics
from locales.texts import get_text
from config import SUPPORTED_LANGUAGES, ADMIN_IDS, SECRET_PROMO_CODE

logger = logging.getLogger(__name__)

async def track_safely(user_id: int, event_name: str, data: dict = None):
    try: 
        await metrics.track_event(user_id, event_name, data)
    except Exception as e:
        logger.debug(f"Metrics tracking failed: {e}")

def safe_format_text(text: str) -> str:
    """Safely formats text, handling None values"""
    if not text: 
        return ""
    text = re.sub(r'#{1,6}\s*(.*?)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    return text

def get_main_menu_keyboard(lang: str, is_premium: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    favorites_text = get_text(lang, "btn_favorites") or "⭐️ Favorites"
    builder.row(InlineKeyboardButton(text=favorites_text, callback_data="show_favorites"))
    
    if not is_premium:
        premium_text = get_text(lang, "btn_buy_premium") or "💎 Get Premium"
        builder.row(InlineKeyboardButton(text=premium_text, callback_data="buy_premium"))
    
    lang_text = get_text(lang, "btn_change_lang") or "🌐 Language"
    help_text = get_text(lang, "btn_help") or "❓ Help"
    
    builder.row(
        InlineKeyboardButton(text=lang_text, callback_data="change_language"),
        InlineKeyboardButton(text=help_text, callback_data="show_help")
    )
    return builder.as_markup()

# --- START (AUTO DETECT LANGUAGE + CLEAN UI) ---
async def cmd_start(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username
    
    # 1. Auto-detect language from Telegram
    tg_lang = message.from_user.language_code
    if tg_lang and tg_lang in SUPPORTED_LANGUAGES:
        lang_to_save = tg_lang
    else:
        lang_to_save = 'en'
    
    # Save user with detected language
    await users_repo.get_or_create(user_id, first_name, username, language=lang_to_save)
    
    # Get fresh user data
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', lang_to_save)
    
    welcome_text = get_text(lang, "welcome", name=html.quote(first_name))
    if not welcome_text:
        welcome_text = f"👋 Welcome, {html.quote(first_name)}! Send ingredients or ask for a recipe."
    
    formatted_text = safe_format_text(welcome_text)
    
    # NO BUTTONS - Clean UI
    await message.answer(formatted_text, parse_mode="HTML")
    
    await track_safely(user_id, "start_command", {"language": lang, "detected": tg_lang})
    
    # Gift Logic
    if user_data.get('trial_status') == 'pending':
        created_at = user_data.get('created_at')
        if created_at:
            now = datetime.now(created_at.tzinfo if created_at.tzinfo else timezone.utc)
            if (now - created_at).total_seconds() < 120:
                await asyncio.sleep(2)
                gift_text = get_text(lang, "welcome_gift_alert")
                if gift_text:
                    await message.answer(safe_format_text(gift_text), parse_mode="HTML")

# --- SET LANGUAGE (CLEAN UI) ---
async def handle_set_language(c: CallbackQuery):
    try:
        l_code = c.data.split("_")[2]
        await users_repo.update_language(c.from_user.id, l_code)
        
        final_lang = l_code
        welcome_text = get_text(final_lang, "welcome", name=html.quote(c.from_user.first_name))
        if not welcome_text:
            welcome_text = f"👋 Welcome back, {html.quote(c.from_user.first_name)}!"
        
        formatted_text = safe_format_text(welcome_text)
        
        # NO BUTTONS - Clean screen
        await c.message.edit_text(text=formatted_text, reply_markup=None, parse_mode="HTML")
        
        await track_safely(c.from_user.id, "language_changed", {"language": l_code})
        
        lang_changed_text = get_text(final_lang, "lang_changed") or "🌐 Language changed"
        await c.answer(lang_changed_text)
    except Exception as e:
        logger.error(f"Language change error: {e}")
        await c.answer("Error changing language")

# --- SHOW FAVORITES ---
async def handle_show_favorites(c: CallbackQuery):
    try:
        from handlers.favorites import handle_favorite_pagination
        await handle_favorite_pagination(c)
    except Exception as e:
        logger.error(f"Show favorites error: {e}")
        await c.answer("Error loading favorites")

# --- RESTART (CLEAN UI) ---
async def handle_restart(c: CallbackQuery):
    try:
        uid = c.from_user.id
        ud = await users_repo.get_user(uid)
        lang = ud.get('language_code', 'en')
        
        welcome_text = get_text(lang, "welcome", name=html.quote(c.from_user.first_name))
        if not welcome_text:
            welcome_text = f"👋 Welcome back, {html.quote(c.from_user.first_name)}!"
        
        w = safe_format_text(welcome_text)
        
        # Remove buttons on restart (like /start)
        try: 
            await c.message.edit_text(w, reply_markup=None, parse_mode="HTML")
        except: 
            await c.message.answer(w, parse_mode="HTML")
        
        await c.answer()
    except Exception as e:
        logger.error(f"Restart error: {e}")
        await c.answer("Error restarting")

# --- MAIN MENU ---
async def handle_main_menu(c: CallbackQuery): 
    try:
        uid = c.from_user.id
        ud = await users_repo.get_user(uid)
        lang = ud.get('language_code', 'en')
        
        # Use "Menu" title since we need buttons here
        menu_text = get_text(lang, "menu") or "🍴 **Main Menu**"
        txt = safe_format_text(menu_text)
        kb = get_main_menu_keyboard(lang, ud.get('is_premium', False))
        
        try: 
            await c.message.edit_text(txt, reply_markup=kb, parse_mode="HTML")
        except: 
            await c.message.answer(txt, reply_markup=kb, parse_mode="HTML")
        
        await c.answer()
    except Exception as e:
        logger.error(f"Main menu error: {e}")
        await c.answer("Error loading menu")

async def cmd_favorites(m: Message):
    try:
        uid = m.from_user.id
        user_data = await users_repo.get_user(uid)
        lang = user_data.get('language_code', 'en')
        
        # Get favorites with proper error handling
        favorites_result = await favorites_repo.get_favorites_page(uid, 1)
        
        # Handle different return types
        if isinstance(favorites_result, tuple) and len(favorites_result) == 2:
            favs, p = favorites_result
        else:
            # Fallback if function returns different format
            favs = favorites_result or []
            p = 1
        
        if not favs:
            empty_text = get_text(lang, "favorites_empty") or "😔 List is empty."
            await m.answer(empty_text)
            return
        
        header_text = get_text(lang, "favorites_title") or "⭐️ **Favorites**"
        head = safe_format_text(header_text) + f" (1/{p})"
        
        b = InlineKeyboardBuilder()
        for f in favs:
            date_str = f['created_at'].strftime('%d.%m') if f.get('created_at') else ""
            btn_text = f"{f['dish_name']} ({date_str})"
            b.row(InlineKeyboardButton(text=btn_text, callback_data=f"view_fav_{f['id']}"))
        
        if p > 1: 
            b.row(InlineKeyboardButton(text="➡️", callback_data="fav_page_2"))
        
        back_text = get_text(lang, "btn_back") or "⬅️ Back"
        b.row(InlineKeyboardButton(text=back_text, callback_data="main_menu"))
        
        await m.answer(head, reply_markup=b.as_markup(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Favorites command error: {e}")
        error_msg = "Error loading favorites"
        await m.answer(error_msg)

async def cmd_lang(m: Message): 
    try:
        uid = m.from_user.id
        user_data = await users_repo.get_user(uid)
        lang = user_data.get('language_code', 'en')
        
        choose_text = get_text(lang, "choose_language") or "🌐 **Choose Language:**"
        b = InlineKeyboardBuilder()
        
        for l in SUPPORTED_LANGUAGES:
            lbl = get_text(lang, f"lang_{l}")
            if not lbl:
                # Fallback names
                fallback_names = {
                    "en": "🇬🇧 English",
                    "de": "🇩🇪 Deutsch", 
                    "fr": "🇫🇷 Français",
                    "it": "🇮🇹 Italiano",
                    "es": "🇪🇸 Español"
                }
                lbl = fallback_names.get(l, l.upper())
            
            if l == lang: 
                lbl = f"✅ {lbl}"
            
            b.row(InlineKeyboardButton(text=lbl, callback_data=f"set_lang_{l}"))
        
        back_text = get_text(lang, "btn_back") or "⬅️ Back"
        b.row(InlineKeyboardButton(text=back_text, callback_data="main_menu"))
        
        await m.answer(safe_format_text(choose_text), reply_markup=b.as_markup(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Language command error: {e}")
        await m.answer("Error loading language menu")

async def handle_change_language(c: CallbackQuery):
    await cmd_lang(c.message)

async def cmd_help(m: Message):
    try:
        uid = m.from_user.id
        user_data = await users_repo.get_user(uid)
        lang = user_data.get('language_code', 'en')
        
        help_title = get_text(lang, 'help_title') or "❓ **Help**"
        help_text_content = get_text(lang, 'help_text') or "Send ingredients to get recipe ideas."
        
        b = InlineKeyboardBuilder()
        back_text = get_text(lang, "btn_back") or "⬅️ Back"
        b.row(InlineKeyboardButton(text=back_text, callback_data="main_menu"))
        
        response = f"<b>{safe_format_text(help_title)}</b>\n\n{safe_format_text(help_text_content)}"
        await m.answer(response, reply_markup=b.as_markup(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Help command error: {e}")
        await m.answer("Error loading help")

async def handle_show_help(c: CallbackQuery): 
    await cmd_help(c.message)

async def cmd_code(m: Message):
    try:
        uid = m.from_user.id
        user_data = await users_repo.get_user(uid)
        lang = user_data.get('language_code', 'en')
        
        args = m.text.split()
        if len(args) < 2: 
            instruction = get_text(lang, "promo_instruction") or "ℹ️ Use: <code>/code CODE</code>"
            await m.answer(safe_format_text(instruction), parse_mode="HTML")
            return
        
        if args[1].strip() == SECRET_PROMO_CODE:
            if await users_repo.activate_premium(uid, 365*99):
                await m.answer("💎 Success! Premium activated for 99 years.", parse_mode="HTML")
                await track_safely(uid, "premium_activated", {"method": "promo"})
            else:
                await m.answer("❌ Activation failed")
        else: 
            await m.answer("🚫 Invalid code.")
    except Exception as e:
        logger.error(f"Code command error: {e}")
        await m.answer("Error processing code")

async def cmd_stats(m: Message):
    try:
        uid = m.from_user.id
        st = await users_repo.get_usage_stats(uid)
        if not st: 
            await m.answer("No statistics available")
            return
        
        user_data = await users_repo.get_user(uid)
        lang = user_data.get('language_code', 'en')
        
        stat = "💎 PREMIUM" if st.get('is_premium') else "👤 FREE"
        txt = f"📊 <b>Statistics</b>\n\n{stat}\n" \
              f"TEXT: {st['text_requests_used']}/{st['text_requests_limit']}\n" \
              f"VOICE: {st['voice_requests_used']}/{st['voice_requests_limit']}"
        
        b = InlineKeyboardBuilder()
        if not st.get('is_premium'):
            premium_text = get_text(lang, "btn_buy_premium") or "💎 Get Premium"
            b.row(InlineKeyboardButton(text=premium_text, callback_data="buy_premium"))
        
        back_text = get_text(lang, "btn_back") or "⬅️ Back"
        b.row(InlineKeyboardButton(text=back_text, callback_data="main_menu"))
        
        await m.answer(txt, reply_markup=b.as_markup(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Stats command error: {e}")
        await m.answer("Error loading statistics")

async def cmd_admin(m: Message):
    try:
        if m.from_user.id in ADMIN_IDS: 
            await m.answer("Admin commands:\n/stats - User stats\n/users - List users\n/reset [ID] - Reset user limits")
        else:
            await m.answer("Access denied")
    except Exception as e:
        logger.error(f"Admin command error: {e}")

async def handle_buy_premium(c: CallbackQuery):
    try:
        user_data = await users_repo.get_user(c.from_user.id)
        lang = user_data.get('language_code', 'en')
        
        b = InlineKeyboardBuilder()
        b.row(InlineKeyboardButton(text="1 Month - 100 ⭐️", callback_data="premium_1_month"))
        b.row(InlineKeyboardButton(text="3 Months - 250 ⭐️ (-17%)", callback_data="premium_3_months"))
        b.row(InlineKeyboardButton(text="1 Year - 800 ⭐️ (-33%)", callback_data="premium_1_year"))
        
        back_text = get_text(lang, "btn_back") or "⬅️ Back"
        b.row(InlineKeyboardButton(text=back_text, callback_data="main_menu"))
        
        premium_desc = get_text(lang, "premium_description")
        if not premium_desc:
            premium_desc = "💎 **Premium Benefits:**\n✅ Unlimited favorites\n✅ Nutrition facts\n✅ Higher limits\n👇 Choose a plan:"
        
        await c.message.edit_text(safe_format_text(premium_desc), reply_markup=b.as_markup(), parse_mode="HTML")
        await c.answer()
    except Exception as e:
        logger.error(f"Buy premium error: {e}")
        await c.answer("Error loading premium options")

# Payment Logic (Stubs - needs implementation)
from aiogram.types import LabeledPrice

async def handle_premium_buy_action(c: CallbackQuery):
    try:
        # This is a stub - implement real payment logic
        plan_map = {
            "premium_1_month": ("1 Month Premium", 100),
            "premium_3_months": ("3 Months Premium", 250),
            "premium_1_year": ("1 Year Premium", 800)
        }
        
        plan_name, price = plan_map.get(c.data, ("Premium", 100))
        
        # Note: Real implementation needs provider_token from payment provider
        await c.message.answer(
            f"⚠️ Payment system not configured.\n\n"
            f"Plan: {plan_name}\n"
            f"Price: {price} ⭐️\n\n"
            f"Contact admin for manual activation.",
            parse_mode="HTML"
        )
        await c.answer()
    except Exception as e:
        logger.error(f"Premium buy action error: {e}")
        await c.answer("Error processing payment")

async def on_pre_checkout_query(q: PreCheckoutQuery):
    await q.answer(ok=True)

async def on_successful_payment(m: Message):
    try:
        p = m.successful_payment.invoice_payload
        days = 30
        if "90" in p: 
            days = 90
        elif "365" in p: 
            days = 365
        
        if await users_repo.activate_premium(m.from_user.id, days):
            for adm in ADMIN_IDS:
                try: 
                    await m.bot.send_message(adm, f"💰 Sale! {days} days for user {m.from_user.id}")
                except: 
                    pass
            
            await m.answer(f"🌟 Success! Premium activated for {days} days.")
        else:
            await m.answer("❌ Activation failed. Contact admin.")
    except Exception as e:
        logger.error(f"Successful payment error: {e}")
        await m.answer("Error processing payment")

async def handle_noop(c: CallbackQuery):
    await c.answer()

def register_common_handlers(dp: Dispatcher):
    """Register all common handlers"""
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
    dp.callback_query.register(handle_premium_buy_action, F.data.startswith("premium_"))
    dp.pre_checkout_query.register(on_pre_checkout_query)
    dp.message.register(on_successful_payment, F.content_type == ContentType.SUCCESSFUL_PAYMENT)
