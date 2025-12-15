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
    
    if not allowed:
        # Получаем язык для сообщения об ошибке
        user_data = await users_repo.get_user(user_id)
        lang = user_data.get('language_code', 'ru') if user_data else 'ru'
        
        await message.answer(
            f"? <b>Лимит исчерпан!</b>\n\n"
            f"Вы использовали {used} из {limit} голосовых запросов сегодня.\n"
            f"Лимиты обновляются каждый день в 00:00.\n\n"
            f"?? <b>Хотите больше?</b> Используйте команду /stats",
            parse_mode="HTML"
        )
        return
    
    # Получаем язык пользователя
    user_data = await users_repo.get_user(user_id)
    lang = user_data.get('language_code', 'ru') if user_data else 'ru'
    
    try:
        # Скачиваем голосовое сообщение
        file_id = message.voice.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        
        # Создаем временный файл
        temp_ogg_path = f"temp/voice_{user_id}_{file_id}.ogg"
        os.makedirs("temp", exist_ok=True)
        
        # Скачиваем файл
        await message.bot.download_file(file_path, temp_ogg_path)
        
        # Конвертируем и распознаем
        text = await voice_service.process_voice(temp_ogg_path, lang)
        
        # Удаляем временный файл
        os.remove(temp_ogg_path)
        
        # Удаляем голосовое сообщение (опционально)
        try:
            await message.delete()
        except:
            pass
        
        # Если текст не распознан
        if not text or len(text.strip()) < 2:
            await message.answer(get_text(lang, "error_voice"))
            return
        
        # Логируем успешное распознавание
        await metrics.track_voice_processed(user_id, True, lang)
        
        # Обрабатываем текст как продукты
        await process_voice_text(message, user_id, text, lang)
        
    except Exception as e:
        logger.error(f"Ошибка обработки голосового сообщения: {e}")
        await message.answer(get_text(lang, "error_voice"))
        
        # Логируем ошибку
        await metrics.track_voice_processed(user_id, False, lang)

async def process_voice_text(message: Message, user_id: int, text: str, lang: str):
    """Обрабатывает распознанный текст из голосового сообщения"""
    # Обрезаем текст до 1000 символов
    if len(text) > 1000:
        text = text[:1000]
    
    # Получаем текущие продукты из состояния
    current_products = state_manager.get_products(user_id)
    
    # Если продуктов ещё нет, проверяем валидность
    if not current_products:
        is_valid = await groq_service.validate_ingredients(text, lang)
        if not is_valid:
            await message.answer(get_text(lang, "error_no_products"))
            return
        
        # Сохраняем продукты
        state_manager.set_products(user_id, text)
        await message.answer(get_text(lang, "products_accepted", products=text))
        
        # Анализируем категории
        await analyze_and_show_categories(message, user_id, text, lang)
    else:
        # Добавляем к существующим продуктам
        state_manager.append_products(user_id, text)
        all_products = state_manager.get_products(user_id)
        await message.answer(get_text(lang, "products_added", products=text))
        
        # Показываем категории с учётом новых продуктов
        await analyze_and_show_categories(message, user_id, all_products, lang)
    
    # Обновляем активность пользователя
    await users_repo.update_activity(user_id)

async def analyze_and_show_categories(message: Message, user_id: int, products: str, lang: str):
    """Анализирует продукты и показывает категории"""
    wait_msg = await message.answer(get_text(lang, "processing"))
    
    try:
        # Анализируем категории
        categories = await groq_service.analyze_products(products, lang)
        
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
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа категорий: {e}")
        await wait_msg.delete()
        await message.answer(get_text(lang, "error_generation"))

def register_voice_handlers(dp: Dispatcher):
    dp.message.register(handle_voice_message, F.voice)