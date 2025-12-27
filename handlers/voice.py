import logging
import os
from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram import types
from database.users import users_repo
from database.metrics import metrics
from services.voice_service import VoiceService
from services.groq_service import groq_service
from locales.texts import get_text
from state_manager import state_manager
from handlers.recipes import parse_direct_request, generate_and_send_recipe # ИМПОРТ

logger = logging.getLogger(__name__)
voice_service = VoiceService()

async def track_safely(user_id: int, event_name: str, data: dict = None):
    try: await metrics.track_event(user_id, event_name, data)
    except: pass

async def handle_voice_message(message: Message):
    user_id = message.from_user.id
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'en')
    
    limit_check_result = await users_repo.check_and_increment_request(user_id, "voice")
if not limit_check_result[0]:  # Если success == False
    await message.answer(get_text(lang, "limit_voice_exceeded"), parse_mode="HTML")
    return

    wait_msg = await message.answer(get_text(lang, "processing"))
    temp_path = None
    
    try:
        file = await message.bot.get_file(message.voice.file_id)
        temp_path = f"{os.getcwd()}/{message.voice.file_id}.ogg"
        await message.bot.download_file(file.file_path, temp_path)
        
        text = await voice_service.process_voice(temp_path, lang)
        
        if not text:
            await wait_msg.delete()
            await message.answer(get_text(lang, "error_voice_recognition"))
            return
            
        await wait_msg.delete()
        await message.answer(get_text(lang, "voice_recognized").format(text=text))

        # --- 1. ПРЯМОЙ ЗАПРОС? ---
        direct_dish = parse_direct_request(text)
        if direct_dish:
            state_manager.set_products(user_id, "")
            await generate_and_send_recipe(message, user_id, direct_dish, "", lang, is_direct=True)
            await track_safely(user_id, "voice_command_success", {"cmd": text})
            return

        # --- 2. АНАЛИЗ (Dict: categories + suggestion) ---
        state_manager.set_products(user_id, text)
        wait_msg = await message.answer(get_text(lang, "processing"))
        
        analysis_result = await groq_service.analyze_products(text, lang)
        await wait_msg.delete()
        
        if not analysis_result or not analysis_result.get("categories"):
            await message.answer(get_text(lang, "error_not_enough_products"))
            return
        
        categories = analysis_result["categories"]
        suggestion = analysis_result.get("suggestion")

        state_manager.set_categories(user_id, categories)
        
        # Показываем умный совет
        if suggestion:
             await message.answer(suggestion)
             
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        for cat in categories:
             builder.row(types.InlineKeyboardButton(text=get_text(lang, cat), callback_data=f"cat_{cat}"))
        builder.row(types.InlineKeyboardButton(text=get_text(lang, "btn_restart"), callback_data="restart"))
        await message.answer(get_text(lang, "choose_category"), reply_markup=builder.as_markup())
        
        await track_safely(user_id, "voice_recognized_success", {"lang": lang})

    except Exception as e:
        logger.error(f"Voice error: {e}", exc_info=True)
        try: await wait_msg.delete()
        except: pass
        await message.answer(get_text(lang, "error_generation"))
    finally:
        if temp_path and os.path.exists(temp_path): os.unlink(temp_path)

def register_voice_handlers(dp: Dispatcher):
    dp.message.register(handle_voice_message, F.voice)