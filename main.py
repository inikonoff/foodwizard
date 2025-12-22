import asyncio
import os
import logging
import sys
import contextlib
from datetime import datetime, time, timedelta
import pytz

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
from config import TELEGRAM_TOKEN, LOG_FILE, LOG_LEVEL, validate_config
# from config import ADMIN_IDS
from database import db
from database.metrics import metrics
from database.cache import groq_cache
from database.users import users_repo 
from handlers import register_all_handlers
from services.groq_service import groq_service 

MSK_TZ = pytz.timezone('Europe/Moscow')

def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger('aiogram').setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

# --- ВЕБ-СЕРВЕР ---
async def health_check(request: web.Request):
    return web.Response(text="Bot is alive")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port) 
    await site.start()
    logger.info(f"✅ Web server on port {port}")

# --- ФОНОВЫЕ ЗАДАЧИ (БЕЗ ИЗМЕНЕНИЙ) ---
async def check_premium_expiry_periodically():
    while True:
        try:
            # Логика из вашего старого кода...
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            break

async def cleanup_tasks_periodically():
    while True:
        try:
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            break

# --- ЖИЗНЕННЫЙ ЦИКЛ ---
async def on_startup(bot: Bot):
    """Выполняется при старте"""
    commands = [BotCommand(command="start", description="Запустить бота")]
    await bot.set_my_commands(commands)
    
    for admin_id in ADMIN_IDS:
        with contextlib.suppress(Exception):
            await bot.send_message(admin_id, "✅ Бот перезапущен!")

@contextlib.asynccontextmanager
async def lifespan():
    logger.info("🔗 Подключение к БД...")
    await db.connect()
    
    premium_task = asyncio.create_task(check_premium_expiry_periodically()) 
    cleanup_task = asyncio.create_task(cleanup_tasks_periodically()) 

    try:
        yield
    finally:
        logger.info("🧹 Закрытие ресурсов...")
        premium_task.cancel()
        cleanup_task.cancel()
        await groq_service.close()
        await db.close()

# --- ГЛАВНЫЙ ЗАПУСК ---
async def main():
    logger.info("🚀 Подготовка к запуску...")

    # 1. РЕГИСТРАЦИЯ ХЕНДЛЕРОВ ДО ПОЛЛИНГА (КРИТИЧНО)
    register_all_handlers(dp)
    logger.info("✅ Обработчики зарегистрированы.")

    # 2. Веб-сервер
    await start_web_server()

    async with lifespan():
        # Регистрируем событие стартапа
        dp.startup.register(on_startup)

        # 3. Очистка очереди обновлений
        await bot.delete_webhook(drop_pending_updates=True)
        
        logger.info("📡 Запуск Long Polling...")
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
