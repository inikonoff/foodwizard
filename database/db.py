import asyncpg
import json # <-- Необходим для кодеков
from contextlib import asynccontextmanager
from typing import Optional
from config import DATABASE_URL

class DatabaseManager:
    """Управляет пулом соединений с базой данных."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Создает пул соединений и устанавливает кодеки для JSONB."""
        if not self.pool:
            
            # --- КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ФУНКЦИЯ ИНИЦИАЛИЗАЦИИ КОДЕКОВ ---
            def _init_conn(conn):
                """Устанавливает кодеки для правильной обработки типов JSONB."""
                import json # Импортируем внутри, чтобы избежать проблем с asyncpg
                
                # Принудительно устанавливаем JSONB кодек, чтобы asyncpg знал, что 
                # нужно сериализовать dict/list в JSON, а не просто в текст (str)
                conn.set_type_codec(
                    'jsonb', 
                    encoder=json.dumps, 
                    decoder=json.loads, 
                    schema='pg_catalog'
                )
            # -------------------------------------------------------------
            
            self.pool = await asyncpg.create_pool(
                dsn=DATABASE_URL,
                min_size=1,
                max_size=10, 
                timeout=30,
                init=_init_conn # <-- Используем функцию для настройки каждого соединения в пуле
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