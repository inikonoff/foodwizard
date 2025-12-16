"""
Модуль для работы с подключением к базе данных
Использует пул соединений asyncpg с отключенным кэшем подготовленных выражений
для совместимости с pgbouncer (используется в Supabase)
"""
import asyncpg
import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def connect():
    """
    Создает пул подключений к базе данных.
    """
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL не указан в переменных окружения")

        logger.info("🔧 Создание пула подключений к базе данных...")

        # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: statement_cache_size=0 для совместимости с pgbouncer
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=10,
            statement_cache_size=0,
            command_timeout=60,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )

        logger.info("✅ Пул подключений создан")
    return _pool


async def close():
    """
    Закрывает пул подключений.
    """
    global _pool
    if _pool:
        logger.info("🔧 Закрытие пула подключений...")
        await _pool.close()
        _pool = None
        logger.info("✅ Пул подключений закрыт")


def get_pool():
    """
    Возвращает текущий пул подключений.
    """
    if _pool is None:
        raise RuntimeError("Пул подключений не инициализирован. Вызовите connect() сначала.")
    return _pool


class ConnectionManager:
    """
    Контекстный менеджер для работы с соединениями из пула.
    """

    def __init__(self, pool):
        self.pool = pool
        self.conn = None

    async def __aenter__(self):
        self.conn = await self.pool.acquire()
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            await self.pool.release(self.conn)
            self.conn = None


def connection():
    """
    Возвращает контекстный менеджер для работы с соединением из пула.
    """
    pool = get_pool()
    return ConnectionManager(pool)


async def test_connection():
    """
    Тестирует подключение к базе данных.
    Возвращает True если подключение успешно.
    """
    try:
        async with connection() as conn:
            await conn.fetch("SELECT 1")
            logger.info("✅ Подключение к базе данных успешно")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False

# Глобальный экземпляр для импорта
db = __import__(os.path.basename(__file__).replace('.py', '')) # Динамический импорт для корректного именования