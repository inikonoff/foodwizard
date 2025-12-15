import logging
import os
from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

from database.users import users_repo
from database.metrics import metrics
from services.voice_service import VoiceService
from services.groq_service import groq_service
from locales.texts import get_text
from state_manager import state_manager

logger = logging.getLogger(__name__)
voice_service = VoiceService()

async def handle_voice_message(message: Message):
    user_id = message.from_user.id
    
    # à®¢¥àï¥¬ «¨¬¨âë ­  £®«®á®¢ë¥ á®®¡é¥­¨ï
    allowed, used, limit = await users_repo.check_and_increment_request(user_id, "voice")
    
    if not allowed:
        # ®«ãç ¥¬ ï§ëª ¤«ï á®®¡é¥­¨ï ®¡ ®è¨¡ª¥
        user_data = await users_repo.get_user(user_id)
        lang = user_data.get('language_code', 'ru') if user_data else 'ru'
        
        await message.answer(
            f"? <b>‹¨¬¨â ¨áç¥à¯ ­!</b>\n\n"
            f"‚ë ¨á¯®«ì§®¢ «¨ {used} ¨§ {limit} £®«®á®¢ëå § ¯à®á®¢ á¥£®¤­ï.\n"
            f"‹¨¬¨âë ®¡­®¢«ïîâáï ª ¦¤ë© ¤¥­ì ¢ 00:00.\n\n"
            f"?? <b>•®â¨â¥ ¡®«ìè¥?</b> ˆá¯®«ì§ã©â¥ ª®¬ ­¤ã /stats",
            parse_mode="HTML"
        )
        return
    
    # ®«ãç ¥¬ ï§ëª ¯®«ì§®¢ â¥«ï
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        # ‘ª ç¨¢ ¥¬ £®«®á®¢®¥ á®®¡é¥­¨¥
        file_id = message.voice.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        
        # ‘®§¤ ¥¬ ¢à¥¬¥­­ë© ä ©«
        temp_ogg_path = f"temp/voice_{user_id}_{file_id}.ogg"
        os.makedirs("temp", exist_ok=True)
        
        # ‘ª ç¨¢ ¥¬ ä ©«
        await message.bot.download_file(file_path, temp_ogg_path)
        
        # Š®­¢¥àâ¨àã¥¬ ¨ à á¯®§­ ¥¬
        text = await voice_service.process_voice(temp_ogg_path, lang)
        
        # “¤ «ï¥¬ ¢à¥¬¥­­ë© ä ©«
        os.remove(temp_ogg_path)
        
        # “¤ «ï¥¬ £®«®á®¢®¥ á®®¡é¥­¨¥ (®¯æ¨®­ «ì­®)
        try:
            await message.delete()
        except:
            pass
        
        # …á«¨ â¥ªáâ ­¥ à á¯®§­ ­
        if not text or len(text.strip()) < 2:
            await message.answer(get_text(lang, "error_voice"))
            return
        
        # ‹®£¨àã¥¬ ãá¯¥è­®¥ à á¯®§­ ¢ ­¨¥
        await metrics.track_voice_processed(user_id, True, lang)
        
        # Ž¡à ¡ âë¢ ¥¬ â¥ªáâ ª ª ¯à®¤ãªâë
        await process_voice_text(message, user_id, text, lang)
        
    except Exception as e:
        logger.error(f"Žè¨¡ª  ®¡à ¡®âª¨ £®«®á®¢®£® á®®¡é¥­¨ï: {e}")
        await message.answer(get_text(lang, "error_voice"))
        
        # ‹®£¨àã¥¬ ®è¨¡ªã
        await metrics.track_voice_processed(user_id, False, lang)

async def process_voice_text(message: Message, user_id: int, text: str, lang: str):
    """Ž¡à ¡ âë¢ ¥â à á¯®§­ ­­ë© â¥ªáâ ¨§ £®«®á®¢®£® á®®¡é¥­¨ï"""
    # Ž¡à¥§ ¥¬ â¥ªáâ ¤® 1000 á¨¬¢®«®¢
    if len(text) > 1000:
        text = text[:1000]
    
    # ®«ãç ¥¬ â¥ªãé¨¥ ¯à®¤ãªâë ¨§ á®áâ®ï­¨ï
    current_products = state_manager.get_products(user_id)
    
    # …á«¨ ¯à®¤ãªâ®¢ ¥éñ ­¥â, ¯à®¢¥àï¥¬ ¢ «¨¤­®áâì
    if not current_products:
        is_valid = await groq_service.validate_ingredients(text, lang)
        if not is_valid:
            await message.answer(get_text(lang, "error_no_products"))
            return
        
        # ‘®åà ­ï¥¬ ¯à®¤ãªâë
        state_manager.set_products(user_id, text)
        await message.answer(get_text(lang, "products_accepted", products=text))
        
        # €­ «¨§¨àã¥¬ ª â¥£®à¨¨
        await analyze_and_show_categories(message, user_id, text, lang)
    else:
        # „®¡ ¢«ï¥¬ ª áãé¥áâ¢ãîé¨¬ ¯à®¤ãªâ ¬
        state_manager.append_products(user_id, text)
        all_products = state_manager.get_products(user_id)
        await message.answer(get_text(lang, "products_added", products=text))
        
        # ®ª §ë¢ ¥¬ ª â¥£®à¨¨ á ãçñâ®¬ ­®¢ëå ¯à®¤ãªâ®¢
        await analyze_and_show_categories(message, user_id, all_products, lang)
    
    # Ž¡­®¢«ï¥¬  ªâ¨¢­®áâì ¯®«ì§®¢ â¥«ï
    await users_repo.update_activity(user_id)

async def analyze_and_show_categories(message: Message, user_id: int, products: str, lang: str):
    """€­ «¨§¨àã¥â ¯à®¤ãªâë ¨ ¯®ª §ë¢ ¥â ª â¥£®à¨¨"""
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    try:
        # €­ «¨§¨àã¥¬ ª â¥£®à¨¨
        categories = await groq_service.analyze_products(products, lang)
        
        await wait_msg.delete()
        
        if not categories:
            await message.answer(get_text(lang, "error_generation"))
            return
        
        # ‘®åà ­ï¥¬ ª â¥£®à¨¨ ¢ á®áâ®ï­¨¨
        state_manager.set_categories(user_id, categories)
        
        # ‘®§¤ ñ¬ ª« ¢¨ âãàã á ª â¥£®à¨ï¬¨
        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.row(
                types.InlineKeyboardButton(
                    text=get_text(lang, category),
                    callback_data=f"cat_{category}"
                )
            )
        
        # Š­®¯ª  á¡à®á 
        builder.row(
            types.InlineKeyboardButton(
                text=get_text(lang, "btn_restart"),
                callback_data="restart"
            )
        )
        
        await message.answer(
            get_text(lang, "choose_category"),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Žè¨¡ª   ­ «¨§  ª â¥£®à¨©: {e}")
        await wait_msg.delete()
        await message.answer(get_text(lang, "error_generation"))

def register_voice_handlers(dp: Dispatcher):
    dp.message.register(handle_voice_message, F.voice)
