import asyncpg
import os
from typing import Optional

_pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        # Важно: statement_cache_size=0 для совместимости с pgbouncer
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=10,
            statement_cache_size=0  # Ключевой параметр!
        )
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None