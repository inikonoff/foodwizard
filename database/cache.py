import logging
import hashlib
import json
from datetime import datetime, timedelta, timezone # <-- timezone импортирован
from . import db
from config import CACHE_TTL_RECIPE, CACHE_TTL_ANALYSIS, CACHE_TTL_VALIDATION, CACHE_TTL_INTENT, CACHE_TTL_DISH_LIST
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

class GroqCache:
    # ... (методы _generate_hash и _get_ttl)

    @staticmethod
    async def get(prompt: str, lang: str, model: str, cache_type: str = 'recipe') -> Optional[str]:
        # ...
        pass
    
    @staticmethod
    async def set(prompt: str, response: str, lang: str, model: str, tokens_used: int, cache_type: str = 'recipe') -> bool:
        """Сохраняет результат в кэше с TTL"""

        ttl = GroqCache._get_ttl(cache_type)
        # ИСПРАВЛЕНО: изменено 'tomezone' на 'timezone'
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl) 
        hash_key = GroqCache._generate_hash(prompt, lang, model)

        async with db.connection() as conn:
            query = """
            INSERT INTO groq_cache (hash, response, language, model, tokens_used, expires_at, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            ON CONFLICT (hash) DO UPDATE
            SET response = EXCLUDED.response,
                tokens_used = EXCLUDED.tokens_used,
                expires_at = EXCLUDED.expires_at,
                created_at = NOW()
            """
            try:
                await conn.execute(
                    query, 
                    hash_key, 
                    response, 
                    lang, 
                    model, 
                    tokens_used, 
                    expires_at
                )
                logger.debug(f"Cache set for key: {hash_key}, type: {cache_type}")
                return True
            except Exception as e:
                logger.error(f"Ошибка при сохранении кэша: {e}")
                return False

    @staticmethod
    async def clear_expired() -> int:
        """Очищает просроченные записи из кэша и возвращает количество удалённых"""
        async with db.connection() as conn:
            query = "DELETE FROM groq_cache WHERE expires_at <= NOW() RETURNING hash"
            rows = await conn.fetch(query)
            logger.info(f"Очищено {len(rows)} просроченных записей кэша")
            return len(rows)

    # ... (метод get_stats)

groq_cache = GroqCache()