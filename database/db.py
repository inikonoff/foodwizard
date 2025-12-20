import asyncpg
from contextlib import asynccontextmanager
from typing import Optional
from config import DATABASE_URL

class DatabaseManager:
    """Управляет пулом соединений с базой данных."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Создает пул соединений. Это ОБЯЗАТЕЛЬНО для асинхронных приложений."""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                dsn=DATABASE_URL,
                min_size=1,  # Минимальное количество соединений
                max_size=10, # Максимальное количество соединений (можно настроить)
                timeout=30    # Таймаут получения соединения из пула
            )

    async def close(self):
        """Закрывает пул соединений."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            
    async def test_connection(self) -> bool:
        """Проверяет работоспособность пула соединений."""
        if not self.pool:
            return False
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    @asynccontextmanager
    async def connection(self):
        """
        Контекстный менеджер для получения соединения из пула.
        Используется в репозиториях: async with db.connection() as conn:
        """
        if not self.pool:
            raise RuntimeError("Пул соединений не инициализирован. Вызовите db.connect() первым.")
        
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)

db = DatabaseManager()