import logging
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from . import db
from config import CACHE_TTL_RECIPE, CACHE_TTL_ANALYSIS, CACHE_TTL_VALIDATION, CACHE_TTL_INTENT, CACHE_TTL_DISH_LIST

logger = logging.getLogger(__name__)

class CacheRepository:
    """Репозиторий для кэширования ответов Groq в БД."""

    def _get_ttl(self, cache_type: str) -> int:
        """Возвращает TTL в секундах в зависимости от типа кэша."""
        if cache_type == "analysis": return CACHE_TTL_ANALYSIS
        if cache_type == "validation": return CACHE_TTL_VALIDATION
        if cache_type == "intent": return CACHE_TTL_INTENT
        if cache_type == "dish_list": return CACHE_TTL_DISH_LIST
        return CACHE_TTL_RECIPE # По умолчанию
        
    def _generate_hash(self, prompt: str, lang: str, model: str) -> str:
        """Генерирует уникальный SHA256 хэш для кэша."""
        key_string = f"{prompt}-{lang}-{model}"
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()

    async def get(self, prompt: str, lang: str, model: str, cache_type: str) -> Optional[str]:
        """Получает ответ из кэша, если он не просрочен."""
        # ИСПРАВЛЕНИЕ: Вызываем _generate_hash
        cache_key = self._generate_hash(prompt, lang, model)
        
        async with db.connection() as conn:
            # Срок действия проверяется на уровне SQL
            query = """
            SELECT response FROM groq_cache 
            WHERE prompt_hash = $1 AND cache_type = $2 AND expires_at > NOW()
            """
            row = await conn.fetchrow(query, cache_key, cache_type)
            return row['response'] if row else None

    async def set(self, prompt: str, response: str, lang: str, model: str, tokens_used: int, cache_type: str) -> None:
        """Устанавливает ответ в кэш."""
        cache_key = self._generate_hash(prompt, lang, model)
        ttl = self._get_ttl(cache_type)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        
        async with db.connection() as conn:
            query = """
            INSERT INTO groq_cache (prompt_hash, response, language, model, tokens_used, cache_type, expires_at, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            ON CONFLICT (prompt_hash, cache_type) DO UPDATE
            SET response = EXCLUDED.response,
                tokens_used = EXCLUDED.tokens_used,
                expires_at = EXCLUDED.expires_at,
                created_at = NOW()
            """
            # NOTE: response должен быть JSONB в БД для этого
            await conn.execute(
                query, 
                cache_key, 
                response, 
                lang, 
                model, 
                tokens_used, 
                cache_type, 
                expires_at
            )

    async def clear_expired(self) -> int:
        """Удаляет просроченные записи из кэша."""
        try:
            async with db.connection() as conn:
                result = await conn.execute("DELETE FROM groq_cache WHERE expires_at < NOW()")
                if result and "DELETE" in result:
                    count_str = result.split(" ")[1]
                    return int(count_str)
                return 0
        except Exception as e:
            logger.error(f"Ошибка при очистке кэша: {e}", exc_info=True)
            return 0

groq_cache = CacheRepository()