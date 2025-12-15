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

# Твои локальные модули
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

# --- Константа часового пояса ---
MSK_TZ = pytz.timezone('Europe/Moscow')


@asynccontextmanager
async def lifespan():
    """Управление жизненным циклом приложения (Startup/Shutdown)"""
    # === ЗАПУСК ===
    logger.info("🚀 Запуск бота...")
    
    # Подключаемся к базе данных
    await db.connect()
    
    # Очищаем старый кэш при запуске
    cleared = await groq_cache.clear_expired()
    logger.info(f"🧹 Очищено {cleared} просроченных записей кэша при старте")
    
    # Очищаем старые метрики
    cleared_metrics = await metrics.cleanup_old_metrics(days_to_keep=30)
    logger.info(f"📊 Очищено {cleared_metrics} старых метрик при старте")
    
    # Проверяем истечение премиума при запуске
    expired = await users_repo.check_premium_expiry()
    if expired > 0:
        logger.info(f"🚫 Деактивировано {expired} просроченных премиум-подписок при старте")
    
    yield
    
    # === ОСТАНОВКА ===
    logger.info("🛑 Остановка бота...")
    await db.close()


async def setup_bot_commands():
    """Настраивает команды бота для разных языков"""
    commands_by_language = {}
    
    # Команды для каждого языка из конфига
    for lang in SUPPORTED_LANGUAGES:
        commands_by_language[lang] = [
            BotCommand(command="/start", description=get_text(lang, "btn_restart")),
            BotCommand(command="/favorites", description=get_text(lang, "btn_favorites")),
            BotCommand(command="/lang", description=get_text(lang, "btn_change_lang")),
            BotCommand(command="/help", description=get_text(lang, "btn_help")),
            BotCommand(command="/stats", description="📊 Статистика"),
            BotCommand(command="/code", description="💎 Активировать премиум"),
        ]
    
    # Добавляем команду /admin только для русского (как в оригинале)
    if "ru" in commands_by_language:
        commands_by_language["ru"].append(
            BotCommand(command="/admin", description="👑 Админ-панель")
        )
    
    # Устанавливаем команды для каждого языка
    for lang, commands in commands_by_language.items():
        try:
            await bot.set_my_commands(
                commands=commands,
                scope=BotCommandScopeDefault(),
                language_code=lang
            )
            logger.info(f"✅ Команды установлены для языка: {lang}")
        except Exception as e:
            logger.error(f"❌ Ошибка установки команд для языка {lang}: {e}", exc_info=True)
    
    # Устанавливаем команды по умолчанию (фоллбэк)
    default_commands = commands_by_language.get(DEFAULT_LANGUAGE, [])
    if default_commands:
        try:
            await bot.set_my_commands(
                commands=default_commands,
                scope=BotCommandScopeDefault()
            )
            logger.info(f"✅ Команды по умолчанию установлены")
        except Exception as e:
            logger.error(f"❌ Ошибка установки команд по умолчанию: {e}", exc_info=True)


async def check_premium_expiry_periodically():
    """Периодически проверяет истечение срока премиума (в 03:00 MSK)"""
    while True:
        try:
            now = datetime.now(MSK_TZ)
            target_time = time(3, 0, 0)
            
            # Создаем дату с учетом таймзоны (Исправлено!)
            target_dt = MSK_TZ.localize(datetime.combine(now.date(), target_time))
            
            # Если время уже прошло сегодня, переносим на завтра
            if now >= target_dt:
                target_dt += timedelta(days=1)
            
            # Вычисляем секунды до запуска
            wait_seconds = (target_dt - now).total_seconds()
            
            logger.info(f"⏳ Следующая проверка премиума через {wait_seconds:.0f} сек. ({target_dt})")
            await asyncio.sleep(wait_seconds)
            
            # --- Выполнение проверки ---
            logger.info("🔄 Начало проверки премиум-подписок...")
            expired_count = await users_repo.check_premium_expiry()
            if expired_count > 0:
                logger.info(f"🚫 Деактивировано {expired_count} просроченных премиум-подписок")
            else:
                logger.info("✅ Просроченных подписок не найдено")
                
            # Пауза, чтобы не зациклиться в той же секунде
            await asyncio.sleep(60)
            
        except asyncio.CancelledError:
            logger.info("⚠️ Задача проверки премиума остановлена")
            break
        except Exception as e:
            logger.error(f"❌ Ошибка в задаче проверки премиума: {e}", exc_info=True)
            await asyncio.sleep(3600)  # При ошибке ждем час


async def cleanup_tasks_periodically():
    """Периодически выполняет задачи очистки"""
    while True:
        try:
            # Запускаем каждый час
            await asyncio.sleep(3600)
            
            logger.info("🧹 Ежечасная очистка кэша...")
            cleared_cache = await groq_cache.clear_expired()
            if cleared_cache > 0:
                logger.info(f"🗑 Очищено {cleared_cache} просроченных записей кэша")
            
            # Очищаем метрики раз в сутки в 04:00 по Москве
            # (Используем MSK_TZ, чтобы не зависеть от времени сервера)
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


async def main():
    """Основная функция запуска бота"""
    # Регистрируем таски, чтобы потом их корректно закрыть
    premium_task = None
    cleanup_task = None
    
    try:
        # Используем контекстный менеджер (lifespan)
        async with lifespan():
            # Настраиваем команды
            await setup_bot_commands()
            
            # Регистрируем обработчики
            register_all_handlers(dp)
            
            # Запускаем фоновые задачи и сохраняем ссылки на них
            premium_task = asyncio.create_task(check_premium_expiry_periodically())
            cleanup_task = asyncio.create_task(cleanup_tasks_periodically())
            
            # Запуск поллинга
            logger.info("🤖 Бот запущен и слушает обновления!")
            await dp.start_polling(bot)
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Бот останавливается пользователем...")
    except Exception as e:
        logger.error(f"☠️ Критическая ошибка при запуске: {e}", exc_info=True)
    finally:
        # Корректная отмена фоновых задач
        logger.info("🛑 Завершение фоновых задач...")
        if premium_task:
            premium_task.cancel()
        if cleanup_task:
            cleanup_task.cancel()
        
        # Даем время на закрытие соединений
        await asyncio.sleep(0.5)
        logger.info("🏁 Работа завершена.")


if __name__ == "__main__":
    # На Windows может потребоваться SelectorEventLoopPolicy, 
    # но на Linux/Render обычно работает Default
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        # Этот блок ловит Ctrl+C до запуска main или после его завершения
        pass
