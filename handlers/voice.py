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
    
    # Проверяем лимиты на голосовые сообщения
    allowed, used, limit = await users_repo.check_and_increment_request(user_id, "voice")
    
    # Получаем язык для сообщения об ошибке
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'

    if not allowed:
        # ИСПОЛЬЗУЕМ ЛОКАЛИЗАЦИЮ
        await message.answer(
            get_text(lang, "voice_limit_exceeded", used=used, limit=limit),
            parse_mode="HTML"
        )
        return

    # Скачивание файла
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    temp_ogg_path = None
    try:
        file_id = message.voice.file_id
        file = await message.bot.get_file(file_id)
        temp_ogg_path = os.path.join(os.getcwd(), f"{file_id}.ogg")
        
        await message.bot.download_file(file.file_path, temp_ogg_path)
        
        # Распознавание голоса
        text = await voice_service.process_voice(temp_ogg_path, lang)

        if not text:
            await wait_msg.delete()
            await message.answer(get_text(lang, "error_voice_recognition"))
            return
            
        # Удаляем сообщение-подтверждение о распознавании, чтобы не засорять чат
        await message.answer(get_text(lang, "voice_recognized").format(text=text))
        
        # Сохраняем продукты в состоянии
        state_manager.set_products(user_id, text)
        
        # Анализируем категории
        categories = await groq_service.analyze_products(text, lang)
        
        await wait_msg.delete()
        
        if not categories:
            await message.answer(get_text(lang, "error_generation"))
            return
        
        # Сохраняем категории в состоянии
        state_manager.set_categories(user_id, categories)
        
        # Создаём клавиатуру с категориями
        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.row(
                types.InlineKeyboardButton(
                    text=get_text(lang, category),
                    callback_data=f"cat_{category}"
                )
            )
        
        # Кнопка сброса
        builder.row(
            types.InlineKeyboardButton(
                text=get_text(lang, "btn_restart"),
                callback_data="restart"
            )
        )
        
        await message.answer(
            get_text(lang, "choose_category"),
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки голосового сообщения: {e}")
        await wait_msg.delete()
        await message.answer(get_text(lang, "error_generation"))
        
    finally:
        # Обязательно удаляем временный файл
        if temp_ogg_path and os.path.exists(temp_ogg_path):
            try:
                os.unlink(temp_ogg_path)
            except Exception as e:
                logger.warning(f"Не удалось удалить временный OGG файл {temp_ogg_path}: {e}")

def register_voice_handlers(dp: Dispatcher):
    """Регистрирует обработчики для голосовых сообщений"""
    dp.message.register(handle_voice_message, F.voice)
    
