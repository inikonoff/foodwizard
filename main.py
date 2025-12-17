import asyncio
import os
import logging
import sys
import contextlib
from datetime import datetime, time, timedelta # Для периодических задач
import pytz # Для периодических задач

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

from config import TELEGRAM_TOKEN, LOG_FILE, LOG_LEVEL, ADMIN_IDS, validate_config, WEBHOOK_URL, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from database import db
from database.metrics import metrics
from database.cache import groq_cache
from database.users import users_repo # Нужен для проверки премиумов
from handlers import register_all_handlers
from locales.texts import get_text
from services.groq_service import groq_service # !!! ДОБАВЛЕН ИМПОРТ !!!

# --- КОНСТАНТЫ И НАСТРОЙКА ЛОГГИРОВАНИЯ ---
MSK_TZ = pytz.timezone('Europe/Moscow')

def setup_logging():
    """Настраивает логирование в файл и STDOUT"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

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
    logging.getLogger('httpx').setLevel(logging.WARNING) # Скрываем логи запросов Groq

setup_logging()
logger = logging.getLogger(__name__)

# --- Инициализация ---
try:
    validate_config()
except ValueError as e:
    logger.error(f"❌ Критическая ошибка конфигурации: {e}")
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

        # Используем os.environ.get('RENDER_EXTERNAL_HOSTNAME') или '0.0.0.0'
        site = web.TCPSite(runner, '0.0.0.0', port) 
        await site.start()
        logger.info(f"✅ WEB SERVER STARTED ON PORT {port}")
    except Exception as e:
        logger.error(f"❌ Error starting web server: {e}", exc_info=True)


# --- ПЕРИОДИЧЕСКИЕ ЗАДАЧИ ---
async def check_premium_expiry_periodically():
    """Периодически проверяет истечение срока премиума (в 03:00 MSK)"""
    while True:
        try:
            now = datetime.now(MSK_TZ)
            target_time = time(3, 0, 0)
            target_dt = MSK_TZ.localize(datetime.combine(now.date(), target_time))
            
            if now >= target_dt:
                target_dt += timedelta(days=1)
            
            wait_seconds = (target_dt - now).total_seconds()
            
            logger.info(f"⏳ Следующая проверка премиума через {wait_seconds:.0f} сек. ({target_dt})")
            await asyncio.sleep(wait_seconds)
            
            logger.info("🔄 Начало проверки премиум-подписок...")
            expired_count = await users_repo.check_premium_expiry()
            if expired_count > 0:
                logger.info(f"🚫 Деактивировано {expired_count} просроченных премиум-подписок")
            else:
                logger.info("✅ Просроченных подписок не найдено")
                
            await asyncio.sleep(60) # Пауза 
            
        except asyncio.CancelledError:
            logger.info("⚠️ Задача проверки премиума остановлена")
            break
        except Exception as e:
            logger.error(f"❌ Ошибка в задаче проверки премиума: {e}", exc_info=True)
            await asyncio.sleep(3600)

async def cleanup_tasks_periodically():
    """Периодически выполняет задачи очистки"""
    while True:
        try:
            await asyncio.sleep(3600) # Ждем час
            
            logger.info("🧹 Ежечасная очистка кэша...")
            cleared_cache = await groq_cache.clear_expired()
            if cleared_cache > 0:
                logger.info(f"🗑 Очищено {cleared_cache} просроченных записей кэша")
            
            current_hour_msk = datetime.now(MSK_TZ).hour
            
            if current_hour_msk == 4:
                logger.info("📊 Суточная очистка метрик...")
                cleared_metrics = await metrics.cleanup_old_metrics(days_to_keep=30)
                if cleared_metrics > 0:
                    logger.info(f"📉 Очищено {cleared_metrics} старых метрик")
            
        except asyncio.CancelledError:
            logger.info("⚠️ Задача очистки остановлена")
            break
        except Exception as e:
            logger.error(f"❌ Ошибка в задачах очистки: {e}", exc_info=True)
            await asyncio.sleep(3600)


# --- НАСТРОЙКА МЕНЮ ---
async def setup_bot_commands(bot: Bot):
    """Устанавливает команды меню для всех языков"""
    # ... (твой оригинальный код setup_bot_commands) ...
    pass # Заглушка, так как ты не прислал этот код из common.py

# --- ФУНКЦИИ ЖИЗНЕННОГО ЦИКЛА DP ---

async def on_startup(dispatcher: Dispatcher, bot: Bot):
    """Выполняется при запуске бота"""
    logger.info("⚙️ Запуск обработчиков...")

    register_all_handlers(dispatcher)
    # await setup_bot_commands(bot) # Лучше вызывать отдельно в main

    # Здесь вызываются потенциально ошибочные функции
    await groq_cache.clear_expired()
    await metrics.cleanup_old_metrics()

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "✅ Бот запущен и готов к работе!")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение администратору {admin_id}: {e}")

async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    """Выполняется при остановке бота"""
    logger.info("🛑 Остановка диспетчера и сессии бота...")
    await dispatcher.storage.close()
    await bot.session.close() # Закрываем сессию aiohttp/httpx
    logger.info("👋 Бот остановлен.")

@contextlib.asynccontextmanager
async def lifespan():
    """Контекстный менеджер для управления жизненным циклом ресурсов"""
    logger.info("🔗 Попытка подключения к базе данных...")
    await db.connect()

    db_ok = await db.test_connection() # Убедись, что db.py имеет test_connection()
    if not db_ok:
        logger.error("❌ Критическая ошибка: Подключение к БД не прошло проверку. Завершение работы.")
        sys.exit(1)

    # Инициализация команд и других ресурсов
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
        await groq_service.close() # !!! ИСПРАВЛЕНИЕ: ЗАКРЫТИЕ КЛИЕНТА !!!
        
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

        logger.info("⏳ Запуск Polling...")
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (KeyboardInterrupt)")
    except Exception as e:
        logger.critical(f"💀 Критическая ошибка при запуске: {e}", exc_info=True)
