import logging
import hashlib
import json
from datetime import datetime, timedelta, timezone
from . import db
from config import CACHE_TTL_RECIPE, CACHE_TTL_ANALYSIS, CACHE_TTL_VALIDATION, CACHE_TTL_INTENT, CACHE_TTL_DISH_LIST
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

class GroqCache:
    @staticmethod
    def _generate_hash(prompt: str, lang: str, model: str) -> str:
        """Генерирует уникальный хеш для запроса.
        
        Ключ кэша должен зависеть от промпта, языка и модели для
        корректной работы многоязычного кэширования.
        """
        data = f"{prompt}_{lang}_{model}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def _get_ttl(cache_type: str) -> int:
        """Возвращает TTL в секундах в зависимости от типа запроса"""
        ttl_map = {
            'recipe': CACHE_TTL_RECIPE,
            'analysis': CACHE_TTL_ANALYSIS,
            'validation': CACHE_TTL_VALIDATION,
            'intent': CACHE_TTL_INTENT, # Добавлено
            'dish_list': CACHE_TTL_DISH_LIST # Добавлено
        }
        return ttl_map.get(cache_type, CACHE_TTL_RECIPE)
    
    @staticmethod
    async def get(prompt: str, lang: str, model: str, cache_type: str = 'recipe') -> Optional[str]:
        """Получает результат из кэша, если он есть и не истёк"""
        async with db.connection() as conn:
            # Используем хеш, зависящий от языка и модели
            hash_key = GroqCache._generate_hash(prompt, lang, model) 
            
            query = """
            SELECT response
            FROM groq_cache
            WHERE hash = $1 AND expires_at > NOW()
            """
            
            # fetchval вернет строку (response) или None
            response = await conn.fetchval(query, hash_key)
            
            if response:
                logger.debug(f"Cache hit for key: {hash_key}")
                return response
            
            logger.debug(f"Cache miss for key: {hash_key}")
            return None
    
    @staticmethod
    async def set(prompt: str, response: str, lang: str, model: str, tokens_used: int, cache_type: str = 'recipe') -> bool:
        """Сохраняет результат в кэше с TTL"""
        
        ttl = GroqCache._get_ttl(cache_type)
        expires_at = datetime.now(tomezone.utc) + timedelta(seconds=ttl)
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
    
    @staticmethod
    async def get_stats() -> Dict[str, Any]:
        """Возвращает статистику кэша"""
        async with db.connection() as conn:
            stats_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as active,
                COUNT(CASE WHEN expires_at <= NOW() THEN 1 END) as expired,
                AVG(LENGTH(response)) as avg_response_size,
                SUM(tokens_used) as total_tokens
            FROM groq_cache
            """
            
            row = await conn.fetchrow(stats_query)
            
            return {
                'total_entries': row['total'] or 0,
                'active_entries': row['active'] or 0,
                'expired_entries': row['expired'] or 0,
                'avg_response_size': round(row['avg_response_size'] or 0, 2),
                'total_tokens_cached': row['total_tokens'] or 0
            }

groq_cache = GroqCache()
