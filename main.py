import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, time, timedelta
import pytz

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import TELEGRAM_TOKEN, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from database import db
from database.users import users_repo
from database.metrics import metrics
from database.cache import groq_cache
from handlers import register_all_handlers
from locales.texts import get_text

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

@asynccontextmanager
async def lifespan():
    """Управление жизненным циклом приложения"""
    # Запуск
    logger.info("🚀 Запуск бота...")
    
    # Подключаемся к базе данных
    await db.connect()
    
    # Тестируем подключение к БД
    db_ok = await db.test_connection()
    if not db_ok:
        logger.error("❌ Не удалось подключиться к базе данных")
        raise ConnectionError("Database connection failed")
    
    # Очищаем старый кэш при запуске (необязательно, но полезно)
    try:
        cleared = await groq_cache.clear_expired()
        if cleared > 0:
            logger.info(f"🧹 Очищено {cleared} просроченных записей кэша при запуске")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось очистить кэш при запуске: {e}")
    
    # Очищаем старые метрики
    try:
        cleared_metrics = await metrics.cleanup_old_metrics(days_to_keep=30)
        if cleared_metrics > 0:
            logger.info(f"📊 Очищено {cleared_metrics} старых метрик")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось очистить метрики: {e}")
    
    # Проверяем истечение премиума при запуске
    try:
        expired = await users_repo.check_premium_expiry()
        if expired > 0:
            logger.info(f"⭐ Деактивировано {expired} просроченных премиум-подписок")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось проверить премиум-подписки: {e}")
    
    logger.info("✅ Инициализация завершена")
    yield
    
    # Завершение работы
    logger.info("🛑 Завершение работы бота...")
    await db.close()
    logger.info("🏁 Работа завершена")

async def setup_bot_commands():
    """Настраивает команды бота для разных языков"""
    commands_by_language = {}
    
    # Команды для каждого языка
    for lang in SUPPORTED_LANGUAGES:
        commands_by_language[lang] = [
            BotCommand(command="/start", description=get_text(lang, "btn_restart")),
            BotCommand(command="/favorites", description=get_text(lang, "btn_favorites")),
            BotCommand(command="/lang", description=get_text(lang, "btn_change_lang")),
            BotCommand(command="/help", description=get_text(lang, "btn_help")),
            BotCommand(command="/stats", description="📊 Статистика"),
            BotCommand(command="/code", description="⭐ Активировать премиум"),
        ]
    
    # Добавляем команду /admin только на русском
    commands_by_language["ru"].append(
        BotCommand(command="/admin", description="🔧 Админ-панель")
    )
    
    # Устанавливаем команды для каждого языка
    for lang, commands in commands_by_language.items():
        try:
            await bot.set_my_commands(
                commands=commands,
                scope=BotCommandScopeDefault(),
                language_code=lang
            )
            logger.info(f"✅ Команды установлены для языка {lang}")
        except Exception as e:
            logger.error(f"❌ Ошибка установки команд для языка {lang}: {e}")
    
    # Устанавливаем команды по умолчанию
    default_commands = commands_by_language.get(DEFAULT_LANGUAGE, [])
    if default_commands:
        try:
            await bot.set_my_commands(
                commands=default_commands,
                scope=BotCommandScopeDefault()
            )
            logger.info(f"✅ Команды по умолчанию установлены")
        except Exception as e:
            logger.error(f"❌ Ошибка установки команд по умолчанию: {e}")

async def check_premium_expiry_periodically():
    """Периодически проверяет истечение срока премиума"""
    while True:
        try:
            # Запускаем в 03:00 каждый день
            tz = pytz.timezone('Europe/Moscow')
            now = datetime.now(tz)
            target_time = time(3, 0, 0)
            
            # Ждём до 03:00
            if now.time() < target_time:
                wait_seconds = (datetime.combine(now.date(), target_time) - now).seconds
            else:
                # Уже после 03:00, ждём до завтра
                tomorrow = now.date() + timedelta(days=1)
                wait_seconds = (datetime.combine(tomorrow, target_time) - now).seconds
            
            logger.info(f"⏳ Следующая проверка премиума через {wait_seconds} секунд")
            await asyncio.sleep(wait_seconds)
            
            # Проверяем истечение премиума
            expired_count = await users_repo.check_premium_expiry()
            if expired_count > 0:
                logger.info(f"⭐ Деактивировано {expired_count} просроченных премиум-подписок")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в задаче проверки премиума: {e}")
            await asyncio.sleep(3600)  # Ждём час при ошибке

async def cleanup_tasks_periodically():
    """Периодически выполняет задачи очистки"""
    while True:
        try:
            # Запускаем каждый час
            await asyncio.sleep(3600)
            
            # Очищаем старый кэш
            cleared_cache = await groq_cache.clear_expired()
            if cleared_cache > 0:
                logger.info(f"🧹 Очищено {cleared_cache} просроченных записей кэша")
            
            # Очищаем старые метрики (раз в день)
            current_hour = datetime.now().hour
            if current_hour == 4:  # В 04:00
                cleared_metrics = await metrics.cleanup_old_metrics(days_to_keep=30)
                if cleared_metrics > 0:
                    logger.info(f"📊 Очищено {cleared_metrics} старых метрик")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в задачах очистки: {e}")
            await asyncio.sleep(3600)

async def main():
    """Основная функция запуска бота"""
    try:
        # Используем контекстный менеджер для управления жизненным циклом
        async with lifespan():
            # Настраиваем команды бота
            await setup_bot_commands()
            
            # Регистрируем все обработчики
            register_all_handlers(dp)
            
            # Запускаем фоновые задачи
            asyncio.create_task(check_premium_expiry_periodically())
            asyncio.create_task(cleanup_tasks_periodically())
            
            # Запускаем бота
            logger.info("🤖 Бот запущен и готов к работе!")
            await dp.start_polling(bot)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💀 Критическая ошибка при запуске: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⏹️ Бот остановлен")
