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
from config import TELEGRAM_TOKEN, LOG_FILE, LOG_LEVEL, ADMIN_IDS, validate_config, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from database import db
from database.metrics import metrics
from database.cache import groq_cache
from database.users import users_repo 
from handlers import register_all_handlers
from locales.texts import get_text, TEXTS # <--- ДОБАВЛЕН ИМПОРТ TEXTS
from services.groq_service import groq_service 

# --- КОНСТАНТЫ И НАСТРОЙКА ЛОГГИРОВАНИЯ ---
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
    logging.getLogger('asyncpg').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
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


# --- 🌐 ВЕБ-СЕРВЕР ---
async def health_check(request: web.Request):
    return web.Response(text="Bot is running OK")

async def start_web_server():
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
async def check_premium_expiry_periodically():
    while True:
        try:
            now = datetime.now(MSK_TZ)
            target_time = time(3, 0, 0)
            target_dt = MSK_TZ.localize(datetime.combine(now.date(), target_time))
            if now >= target_dt:
                target_dt += timedelta(days=1)
            wait_seconds = (target_dt - now).total_seconds()
            logger.info(f"⏳ Следующая проверка премиума через {wait_seconds:.0f} сек.")
            await asyncio.sleep(wait_seconds)
            
            logger.info("🔄 Начало проверки премиум-подписок...")
            expired_count = await users_repo.check_premium_expiry()
            if expired_count > 0:
                logger.info(f"🚫 Деактивировано {expired_count} просроченных премиум-подписок")
                
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"❌ Ошибка в задаче проверки премиума: {e}", exc_info=True)
            await asyncio.sleep(3600)

async def cleanup_tasks_periodically():
    while True:
        try:
            await asyncio.sleep(3600)
            cleared_cache = await groq_cache.clear_expired()
            if cleared_cache > 0:
                logger.info(f"🗑 Очищено {cleared_cache} просроченных записей кэша")
            
            current_hour_msk = datetime.now(MSK_TZ).hour
            if current_hour_msk == 4:
                cleared_metrics = await metrics.cleanup_old_metrics(days_to_keep=30)
                if cleared_metrics > 0:
                    logger.info(f"📉 Очищено {cleared_metrics} старых метрик")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"❌ Ошибка в задачах очистки: {e}", exc_info=True)
            await asyncio.sleep(3600)


# --- НАСТРОЙКА ОПИСАНИЯ БОТА (ВИТРИНА) ---
async def set_bot_description(bot: Bot):
    """Обновляет описание бота в Telegram для разных языков"""
    # 1. Дефолтное описание (Английское)
    try:
        en_texts = TEXTS.get("en", {})
        if en_texts:
            await bot.set_my_short_description(en_texts.get("bot_short_description", ""))
            await bot.set_my_description(en_texts.get("bot_description", ""))
            logger.info("✅ Дефолтное описание установлено (EN)")
    except Exception as e:
        logger.warning(f"Ошибка установки дефолтного описания: {e}")

    # 2. Локализованные описания
    for lang_code in SUPPORTED_LANGUAGES:
        if lang_code in TEXTS:
            try:
                short_desc = TEXTS[lang_code].get("bot_short_description")
                full_desc = TEXTS[lang_code].get("bot_description")
                
                if short_desc:
                    await bot.set_my_short_description(short_desc, language_code=lang_code)
                
                if full_desc:
                    await bot.set_my_description(full_desc, language_code=lang_code)
                    
                logger.info(f"✅ Описание установлено для: {lang_code}")
            except Exception as e:
                logger.warning(f"Ошибка установки описания для {lang_code}: {e}")

# --- НАСТРОЙКА МЕНЮ ---
async def setup_bot_commands(bot: Bot):
    # Упрощенная установка команд
    pass 

# --- ФУНКЦИИ ЖИЗНЕННОГО ЦИКЛА DP ---
async def on_startup(dispatcher: Dispatcher, bot: Bot):
    logger.info("⚙️ Запуск обработчиков...")
    register_all_handlers(dispatcher)
    
    # Настраиваем описание бота в Telegram
    await set_bot_description(bot)
    
    await groq_cache.clear_expired()
    await metrics.cleanup_old_metrics()

    for admin_id in ADMIN_IDS:
        try:
            if admin_id: 
                 await bot.send_message(admin_id, "✅ Бот запущен и готов к работе!")
        except Exception: pass

async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    logger.info("🛑 Остановка...")
    await dispatcher.storage.close()
    await bot.session.close() 
    logger.info("👋 Бот остановлен.")

@contextlib.asynccontextmanager
async def lifespan():
    logger.info("🔗 Подключение к базе данных...")
    await db.connect()

    if not await db.test_connection():
        logger.error("❌ Критическая ошибка: Нет соединения с БД.")
        sys.exit(1)

    logger.info("✅ Ресурсы инициализированы.")
    
    premium_task = asyncio.create_task(check_premium_expiry_periodically()) 
    cleanup_task = asyncio.create_task(cleanup_tasks_periodically()) 
    logger.info("✅ Фоновые задачи запущены.")

    try:
        yield
    finally:
        logger.info("🧹 Очистка ресурсов...")
        premium_task.cancel()
        cleanup_task.cancel()
        await groq_service.close()
        await db.close() 
        logger.info("✅ Ресурсы закрыты.")


# --- ГЛАВНАЯ ФУНКЦИЯ ---
async def main():
    logger.info("🚀 Запуск бота...")
    await start_web_server()

    async with lifespan():
        dp.startup.register(on_startup) 
        dp.shutdown.register(on_shutdown) 

        try:
            await bot.delete_webhook(drop_pending_updates=True) 
            logger.info("✅ Webhook сброшен.")
        except Exception as e:
             logger.warning(f"Ошибка сброса Webhook: {e}")

        logger.info("⏳ Запуск Polling...")
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"💀 Критическая ошибка при запуске: {e}", exc_info=True)