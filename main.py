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

# Импорты локальных модулей
# Убедитесь, что все эти файлы существуют
from config import TELEGRAM_TOKEN, LOG_FILE, LOG_LEVEL, ADMIN_IDS, validate_config
from database import db
from database.metrics import metrics
from database.cache import groq_cache
from database.users import users_repo 
from handlers import register_all_handlers
from services.groq_service import groq_service 
from locales.texts import get_text

# Константы
MSK_TZ = pytz.timezone('Europe/Moscow')

# --- НАСТРОЙКА ЛОГГИРОВАНИЯ ---
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
    # Отключаем лишний шум библиотек
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('asyncpg').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger(__name__)

# --- ИНИЦИАЛИЗАЦИЯ БОТА ---
try:
    validate_config()
except ValueError as e:
    logger.critical(f"❌ Критическая ошибка конфигурации: {e}", exc_info=True)
    sys.exit(1)

bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

# --- 🌐 ВЕБ-СЕРВЕР (Для Health Check Render) ---
async def health_check(request: web.Request):
    return web.Response(text="Bot is running OK")

async def start_web_server():
    """Запускает маленький веб-сервер, чтобы Render не усыплял бота (если настроен Health Check)"""
    try:
        app = web.Application()
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        # Render передает PORT через переменную окружения
        port = int(os.environ.get("PORT", 8080))
        site = web.TCPSite(runner, '0.0.0.0', port) 
        await site.start()
        logger.info(f"✅ WEB SERVER STARTED ON PORT {port}")
    except Exception as e:
        logger.error(f"❌ Error starting web server: {e}", exc_info=True)

# --- ПЕРИОДИЧЕСКИЕ ЗАДАЧИ ---

async def check_premium_expiry_periodically():
    """Проверяет истечение подписки раз в день"""
    while True:
        try:
            # Вычисляем время до 3 ночи
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
                
            await asyncio.sleep(60) # Чтобы не зациклиться
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"❌ Ошибка в задаче проверки премиума: {e}", exc_info=True)
            await asyncio.sleep(3600)

async def cleanup_tasks_periodically():
    """Чистит кэш и метрики"""
    while True:
        try:
            await asyncio.sleep(3600) # Каждый час
            
            # Чистка кэша
            cleared_cache = await groq_cache.clear_expired()
            if cleared_cache > 0:
                logger.info(f"🗑 Очищено {cleared_cache} просроченных записей кэша")
            
            # Чистка метрик (только в 4 утра)
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

async def check_trials_periodically():
    """Раз в час проверяет и выдает подарочный триал"""
    while True:
        try:
            # logger.info("🎁 Проверка триалов...") # Можно раскомментировать для дебага
            user_ids = await users_repo.process_trial_activations()
            
            for uid in user_ids:
                try:
                    user = await users_repo.get_user(uid)
                    lang = user.get('language_code', 'en') # По дефолту EN
                    # Отправляем сообщение
                    await bot.send_message(uid, get_text(lang, "trial_activated_notification"))
                    logger.info(f"🎁 Триал выдан: {uid}")
                    await asyncio.sleep(0.5) # Пауза чтобы не спамить
                except Exception as e:
                    logger.warning(f"Не удалось отправить уведомление о триале юзеру {uid}: {e}")
            
            await asyncio.sleep(3600) # Спим час
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"❌ Ошибка задачи триалов: {e}", exc_info=True)
            await asyncio.sleep(3600)

# --- HOOKS ---

async def on_startup(dispatcher: Dispatcher, bot: Bot):
    logger.info("⚙️ Запуск обработчиков...")
    
    # Регистрация всех хендлеров из папки handlers
    register_all_handlers(dispatcher)
    
    # Первичная очистка при старте
    await groq_cache.clear_expired()
    await metrics.cleanup_old_metrics()

    # Уведомление админа о старте
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

register_all_handlers(dp)

# --- УПРАВЛЕНИЕ ЖИЗНЕННЫМ ЦИКЛОМ (Context Manager) ---
@contextlib.asynccontextmanager
async def lifespan():
    logger.info("🔗 Подключение к базе данных...")
    await db.connect()

    # Проверка соединения с БД
    if not await db.test_connection():
        logger.error("❌ Критическая ошибка: Нет соединения с БД. Проверьте DATABASE_URL.")
        sys.exit(1)

    logger.info("✅ Ресурсы инициализированы.")
    
    # Запуск фоновых задач
    premium_task = asyncio.create_task(check_premium_expiry_periodically()) 
    cleanup_task = asyncio.create_task(cleanup_tasks_periodically()) 
    trial_task = asyncio.create_task(check_trials_periodically())
    logger.info("✅ Фоновые задачи запущены.")

    try:
        yield # Работа бота происходит здесь
    finally:
        logger.info("🧹 Очистка ресурсов...")
        # Отменяем задачи
        premium_task.cancel()
        cleanup_task.cancel()
        trial_task.cancel()
        
        # Закрываем соединения
        await groq_service.close()
        await db.close() 
        logger.info("✅ Ресурсы закрыты.")


# --- ГЛАВНАЯ ФУНКЦИЯ ---
async def main():
    logger.info("🚀 Запуск бота...")
    
    # Запускаем Web-сервер в фоне
    await start_web_server()

    # Запускаем Lifespan (БД, задачи) + Polling
    async with lifespan():
        dp.startup.register(on_startup) 
        dp.shutdown.register(on_shutdown) 

        # Сбрасываем вебхук (чтобы не было конфликтов с предыдущими запусками)
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