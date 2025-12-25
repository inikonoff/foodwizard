import asyncio
import os
import logging
import sys
import contextlib
from datetime import datetime, time, timedelta
import pytz

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

from config import TELEGRAM_TOKEN, LOG_FILE, LOG_LEVEL, validate_config
from database import db
from database.metrics import metrics
from database.cache import groq_cache
from database.users import users_repo 
from handlers import register_all_handlers
from services.groq_service import groq_service 
from locales.texts import get_text

MSK_TZ = pytz.timezone('Europe/Moscow')
# ... (setup_logging) ...
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

# ... (health_check, start_web_server, check_premium_expiry, cleanup) ...

# !!! НОВАЯ ЗАДАЧА !!!
async def check_trials_periodically():
    """Раз в час проверяет и выдает подарки"""
    while True:
        try:
            logger.info("🎁 Проверка триалов...")
            ids = await users_repo.process_trial_activations()
            for uid in ids:
                try:
                    user = await users_repo.get_user(uid)
                    lang = user.get('language_code', 'ru')
                    await bot.send_message(uid, get_text(lang, "trial_activated_notification"))
                except: pass
            await asyncio.sleep(3600)
        except asyncio.CancelledError: break
        except Exception: await asyncio.sleep(3600)

@contextlib.asynccontextmanager
async def lifespan():
    # ... (connect db) ...
    
    prem_task = asyncio.create_task(check_premium_expiry_periodically()) 
    clean_task = asyncio.create_task(cleanup_tasks_periodically()) 
    trial_task = asyncio.create_task(check_trials_periodically()) # ЗАПУСК
    
    try: yield
    finally:
        prem_task.cancel()
        clean_task.cancel()
        trial_task.cancel() # ОТМЕНА
        # ... (close db) ...

# ... (main) ...