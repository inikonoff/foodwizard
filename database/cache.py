import logging
import hashlib
import json
# Используем явные импорты, но только то, что нужно
from datetime import datetime, timedelta, timezone 
from . import db
from config import CACHE_TTL_RECIPE, CACHE_TTL_ANALYSIS, CACHE_TTL_VALIDATION, CACHE_TTL_INTENT, CACHE_TTL_DISH_LIST
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

class GroqCache:
    
    # ... (Остальные методы _generate_hash, _get_ttl, get, clear_expired, get_stats остаются как есть)
    
    @staticmethod
    async def set(prompt: str, response: str, lang: str, model: str, tokens_used: int, cache_type: str = 'recipe') -> bool:
        """Сохраняет результат в кэше с TTL"""
        
        ttl = GroqCache._get_ttl(cache_type)
        
        # --- ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ: Использование прямого импорта datetime и timedelta ---
        # Это гарантирует, что expires_at будет иметь tzinfo=UTC, что Postgres требует.
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        # -----------------------------------------------------------------------------
        
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
                    expires_at # Передача объекта с tzinfo=UTC
                )
                logger.debug(f"Cache set for key: {hash_key}, type: {cache_type}")
                return True
            except Exception as e:
                logger.error(f"Ошибка при сохранении кэша: {e}")
                logger.error(f"Тип expires_at: {type(expires_at)}, значение: {expires_at}, tzinfo: {expires_at.tzinfo}")
                return False

# ... (Остальные методы)

groq_cache = GroqCache()