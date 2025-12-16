import asyncio
import os
import logging
import sys
import contextlib
from aiogram.client.default import DefaultBotProperties # <-- НОВЫЙ ИМПОРТ
from aiogram import Bot, Dispatcher
# ...

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiohttp import web  # <--- НОВЫЙ ИМПОРТ ДЛЯ WEB-СЕРВЕРА

from config import TELEGRAM_TOKEN, LOG_FILE, LOG_LEVEL, ADMIN_IDS, validate_config, WEBHOOK_URL
from database import db
from handlers import register_all_handlers
from database.metrics import metrics
from database.cache import groq_cache
from locales.texts import get_text

# --- НАСТРОЙКА ЛОГГИРОВАНИЯ ---
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
    # Снижаем уровень логов для некоторых библиотек
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('asyncpg').setLevel(logging.WARNING)
    
setup_logging()
logger = logging.getLogger(__name__)

# --- Инициализация ---
try:
    validate_config()
except ValueError as e:
    logger.error(f"❌ Критическая ошибка конфигурации: {e}")
    sys.exit(1)


bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotPriperties(parse_ode='HTML'))

# --- 🌐 ВЕБ-СЕРВЕР ДЛЯ RENDER (HEALTH CHECK) ---
async def health_check(request: web.Request):
    """Ответ на проверку работоспособности"""
    return web.Response(text="Bot is running OK")

async def start_web_server():
    """Запускает заглушку веб-сервера"""
    try:
        app = web.Application()
        # Добавляем маршруты для проверки
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        # Render передает порт через переменную окружения PORT
        # Используем 8080 как дефолт, но лучше брать из os.environ['PORT']
        port = int(os.environ.get("PORT", 8080))
        
        # Запускаем сервер в фоновом режиме
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        logger.info(f"✅ WEB SERVER STARTED ON PORT {port}")
    except Exception as e:
        logger.error(f"❌ Error starting web server: {e}")

# --- ФУНКЦИИ ЖИЗНЕННОГО ЦИКЛА ---

async def on_startup(dispatcher: Dispatcher, bot: Bot):
    """Выполняется при запуске бота"""
    logger.info("⚙️ Запуск обработчиков...")
    
    # Регистрация всех хэндлеров
    register_all_handlers(dispatcher)

    # Настройка команд
    await setup_bot_commands(bot)
    
    # Очистка кэша и метрик
    await groq_cache.clear_expired()
    await metrics.cleanup_old_metrics()
    
    # Сообщаем об успешном запуске администраторам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "✅ Бот запущен и готов к работе!")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение администратору {admin_id}: {e}")

async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    """Выполняется при остановке бота"""
    logger.info("🛑 Остановка бота...")
    await dispatcher.storage.close()
    await bot.session.close()
    await db.close() # Закрываем соединение с БД
    logger.info("👋 Бот остановлен.")
    
# --- НАСТРОЙКА МЕНЮ ---
async def setup_bot_commands(bot: Bot):
    """Устанавливает команды меню"""
    commands = [
        BotCommand(command="start", description=get_text('ru', 'btn_restart')),
        BotCommand(command="favorites", description=get_text('ru', 'btn_favorites')),
        BotCommand(command="lang", description=get_text('ru', 'btn_change_lang')),
        BotCommand(command="help", description=get_text('ru', 'btn_help')),
        BotCommand(command="stats", description="📊 Статистика")
    ]
    try:
        await bot.set_my_commands(commands)
        logger.info("✅ Команды меню установлены.")
    except Exception as e:
        logger.error(f"Не удалось установить команды: {e}")
        
@contextlib.asynccontextmanager
async def lifespan():
    """Контекстный менеджер для управления жизненным циклом ресурсов"""
    logger.info("🔗 Попытка подключения к базе данных...")
    await db.connect()
    
    # Проверка подключения
    db_ok = await db.test_connection()
    if not db_ok:
        logger.error("❌ Критическая ошибка: Подключение к БД не прошло проверку. Завершение работы.")
        sys.exit(1)
    
    logger.info("✅ Ресурсы инициализированы.")
    try:
        yield
    finally:
        logger.info("🧹 Очистка ресурсов...")
        await db.close()

# --- ГЛАВНАЯ ФУНКЦИЯ ---
async def main():
    logger.info("🚀 Запуск бота...")
    
    # 1. Запускаем Web Server
    # Это ключевой момент для Render/Heroku, чтобы открыть порт до старта Polling
    await start_web_server()

    async with lifespan():
        # Регистрация хуков
        dp.startup.register(lambda: on_startup(dp, bot))
        dp.shutdown.register(lambda: on_shutdown(dp, bot))
        
        # 2. Запуск Polling
        # Polling будет блокировать основной поток, пока не будет остановлен
        logger.info("⏳ Запуск Polling...")
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (KeyboardInterrupt)")
    except Exception as e:
        logger.critical(f"💀 Критическая ошибка при запуске: {e}", exc_info=True)

