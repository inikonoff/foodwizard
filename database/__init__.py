import asyncpg
import logging
from typing import Optional
from contextlib import asynccontextmanager

from config import DATABASE_URL

logger = logging.getLogger(__name__)

class Database:
    """Š« áá ¤«ï ã¯à ¢«¥­¨ï ¯®¤ª«îç¥­¨¥¬ ª Supabase"""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def connect(cls):
        """‘®§¤ ñâ ¯ã« ¯®¤ª«îç¥­¨© ª ¡ §¥ ¤ ­­ëå"""
        if cls._pool is None:
            try:
                cls._pool = await asyncpg.create_pool(
                    dsn=DATABASE_URL,
                    min_size=1,
                    max_size=10,
                    command_timeout=60
                )
                logger.info("? ®¤ª«îç¥­¨¥ ª Supabase ãáâ ­®¢«¥­®")
            except Exception as e:
                logger.error(f"? Žè¨¡ª  ¯®¤ª«îç¥­¨ï ª Supabase: {e}")
                raise
    
    @classmethod
    async def close(cls):
        """‡ ªàë¢ ¥â ¯ã« ¯®¤ª«îç¥­¨©"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("? ®¤ª«îç¥­¨¥ ª Supabase § ªàëâ®")
    
    @classmethod
    @asynccontextmanager
    async def connection(cls):
        """Š®­â¥ªáâ­ë© ¬¥­¥¤¦¥à ¤«ï ¯®«ãç¥­¨ï á®¥¤¨­¥­¨ï"""
        await cls.connect()
        async with cls._pool.acquire() as conn:
            yield conn
    
    @classmethod
    async def execute(cls, query: str, *args):
        """‚ë¯®«­ï¥â SQL § ¯à®á"""
        async with cls.connection() as conn:
            return await conn.execute(query, *args)
    
    @classmethod
    async def fetch(cls, query: str, *args):
        """‚ë¯®«­ï¥â § ¯à®á ¨ ¢®§¢à é ¥â ¢á¥ áâà®ª¨"""
        async with cls.connection() as conn:
            return await conn.fetch(query, *args)
    
    @classmethod
    async def fetchrow(cls, query: str, *args):
        """‚ë¯®«­ï¥â § ¯à®á ¨ ¢®§¢à é ¥â ®¤­ã áâà®ªã"""
        async with cls.connection() as conn:
            return await conn.fetchrow(query, *args)
    
    @classmethod
    async def fetchval(cls, query: str, *args):
        """‚ë¯®«­ï¥â § ¯à®á ¨ ¢®§¢à é ¥â ®¤­® §­ ç¥­¨¥"""
        async with cls.connection() as conn:
            return await conn.fetchval(query, *args)

# ƒ«®¡ «ì­ë© íª§¥¬¯«ïà ¤«ï ¨¬¯®àâ 
db = Database()
