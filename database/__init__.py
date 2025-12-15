import asyncpg
import logging
from typing import Optional
from contextlib import asynccontextmanager

from config import DATABASE_URL

logger = logging.getLogger(__name__)

class Database:
    """Класс для управления подключением к Supabase"""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def connect(cls):
        """Создаёт пул подключений к базе данных"""
        if cls._pool is None:
            try:
                cls._pool = await asyncpg.create_pool(
                    dsn=DATABASE_URL,
                    min_size=1,
                    max_size=10,
                    command_timeout=60
                )
                logger.info("? Подключение к Supabase установлено")
            except Exception as e:
                logger.error(f"? Ошибка подключения к Supabase: {e}")
                raise
    
    @classmethod
    async def close(cls):
        """Закрывает пул подключений"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("? Подключение к Supabase закрыто")
    
    @classmethod
    @asynccontextmanager
    async def connection(cls):
        """Контекстный менеджер для получения соединения"""
        await cls.connect()
        async with cls._pool.acquire() as conn:
            yield conn
    
    @classmethod
    async def execute(cls, query: str, *args):
        """Выполняет SQL запрос"""
        async with cls.connection() as conn:
            return await conn.execute(query, *args)
    
    @classmethod
    async def fetch(cls, query: str, *args):
        """Выполняет запрос и возвращает все строки"""
        async with cls.connection() as conn:
            return await conn.fetch(query, *args)
    
    @classmethod
    async def fetchrow(cls, query: str, *args):
        """Выполняет запрос и возвращает одну строку"""
        async with cls.connection() as conn:
            return await conn.fetchrow(query, *args)
    
    @classmethod
    async def fetchval(cls, query: str, *args):
        """Выполняет запрос и возвращает одно значение"""
        async with cls.connection() as conn:
            return await conn.fetchval(query, *args)

# Глобальный экземпляр для импорта
db = Database()
