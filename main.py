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

# Твои модули
from config import TELEGRAM_TOKEN, LOG_FILE, LOG_LEVEL, ADMIN_IDS, validate_config, WEBHOOK_URL, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from database import db
from database.metrics import metrics
from database.cache import groq_cache
from database.users import users_repo 
from handlers import register_all_handlers
from locales.texts import get_text
from services.groq_service import groq_service 

# --- КОНСТАНТЫ И НАСТРОЙКА ЛОГГИРОВАНИЯ ---
MSK_TZ = pytz.timezone('Europe/Moscow')

def setup_logging():
    """Настраивает логирование в файл и STDOUT"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Убедись, что LOG_LEVEL корректно установлен в config
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout) # Важно для Render
        ]
    )
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('asyncpg').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
# Инициализация логирования
setup_logging()
logger = logging.getLogger(__name__)

# --- Инициализация ---
try:
    validate_config()
except ValueError as e:
    logger.error(f"❌ Критическая ошибка конфигурации: {e}", exc_info=True)
    sys.exit(1)

bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()


# --- 🌐 ВЕБ-СЕРВЕР ДЛЯ RENDER (HEALTH CHECK) ---
async def health_check(request: web.Request):
    """Ответ на проверку работоспособности"""
    return web.Response(text="Bot is running OK")

async def start_web_server():
    """Запускает заглушку веб-сервера"""
    try:
        app = web.Application()
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)

        runner = web.AppRunner(app)
        await runner.setup()

        port = int(os.environ.get("PORT", 8080))
        site = web.TCPSite(runner, '0.0.0.0', port) 
        await site.start()
        logger.info(f"✅ WEB SERVER STARTED ON PORT {port}")
    except Exception as e:
        logger.error(f"❌ Error starting web server: {e}", exc_info=True)


# --- ПЕРИОДИЧЕСКИЕ ЗАДАЧИ ---
# (Твой код check_premium_expiry_periodically и cleanup_tasks_periodically здесь...)
# ВНИМАНИЕ: код этих функций я не повторяю, так как он большой, 
# используй исправленные версии, которые я давал ранее!


# --- НАСТРОЙКА МЕНЮ ---
async def setup_bot_commands(bot: Bot):
    """Устанавливает команды меню для всех языков"""
    # (Твой оригинальный код setup_bot_commands)
    # Используй здесь код, который ты писал в common.py (с циклами по языкам)
    pass 

# --- ФУНКЦИИ ЖИЗНЕННОГО ЦИКЛА DP ---

async def on_startup(dispatcher: Dispatcher, bot: Bot):
    """Выполняется при запуске бота"""
    logger.info("⚙️ Запуск обработчиков...")

    register_all_handlers(dispatcher)
    await setup_bot_commands(bot) # Вызов установки команд
    
    # Инициализация кэша и метрик
    await groq_cache.clear_expired()
    await metrics.cleanup_old_metrics()

    for admin_id in ADMIN_IDS:
        try:
            # Используем ID, чтобы не упасть, если admin_id = None или 0
            if admin_id: 
                 await bot.send_message(admin_id, "✅ Бот запущен и готов к работе!")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение администратору {admin_id}: {e}", exc_info=True)

async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    """Выполняется при остановке бота"""
    logger.info("🛑 Остановка диспетчера и сессии бота...")
    await dispatcher.storage.close()
    await bot.session.close() 
    logger.info("👋 Бот остановлен.")

@contextlib.asynccontextmanager
async def lifespan():
    """Контекстный менеджер для управления жизненным циклом ресурсов"""
    logger.info("🔗 Попытка подключения к базе данных...")
    await db.connect()

    db_ok = True # Заглушка, если нет db.test_connection()
    # db_ok = await db.test_connection() # Используй это, если у тебя есть эта функция
    if not db_ok:
        logger.error("❌ Критическая ошибка: Подключение к БД не прошло проверку. Завершение работы.", exc_info=True)
        sys.exit(1)

    logger.info("✅ Ресурсы инициализированы.")
    
    # Запуск фоновых задач
    premium_task = asyncio.create_task(check_premium_expiry_periodically())
    cleanup_task = asyncio.create_task(cleanup_tasks_periodically())
    logger.info("✅ Фоновые задачи запущены.")

    try:
        yield
    finally:
        logger.info("🧹 Очистка ресурсов...")
        
        # Отменяем фоновые задачи
        premium_task.cancel()
        cleanup_task.cancel()
        
        # Закрываем Groq client
        await groq_service.close()
        
        # Закрываем соединение с БД
        await db.close() 
        logger.info("✅ Ресурсы закрыты.")


# --- ГЛАВНАЯ ФУНКЦИЯ ---
async def main():
    logger.info("🚀 Запуск бота...")
    
    # Запуск Web-сервера для Health Check
    await start_web_server()

    async with lifespan():
        # Регистрация обработчиков жизненного цикла
        dp.startup.register(on_startup) 
        dp.shutdown.register(on_shutdown) 

        # !!! ИСПРАВЛЕНИЕ TelegramConflictError !!!
        # Сбрасываем старые Polling-сессии (или Webhook)
        try:
            await bot.delete_webhook(drop_pending_updates=True) 
            logger.info("✅ Старые Polling/Webhook сессии сброшены.")
        except Exception as e:
             logger.warning(f"Ошибка сброса Webhook: {e}")

        logger.info("⏳ Запуск Polling...")
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (KeyboardInterrupt)")
    except Exception as e:
        logger.critical(f"💀 Критическая ошибка при запуске: {e}", exc_info=True)
