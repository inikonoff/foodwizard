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
        """Генерирует уникальный SHA256 хэш на основе входных параметров."""
        data = f"{prompt.strip()}:{lang}:{model}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    @staticmethod
    def _get_ttl(cache_type: str) -> int:
        """Возвращает TTL в секундах на основе типа кэша"""
        ttl_map = {
            'recipe': CACHE_TTL_RECIPE,
            'analysis': CACHE_TTL_ANALYSIS,
            'validation': CACHE_TTL_VALIDATION,
            'intent': CACHE_TTL_INTENT,
            'dish_list': CACHE_TTL_DISH_LIST,
        }
        return ttl_map.get(cache_type, CACHE_TTL_RECIPE)

    @staticmethod
    async def get(prompt: str, lang: str, model: str, cache_type: str = 'recipe') -> Optional[str]:
        """Получает результат из кэша, если он не просрочен"""
        hash_key = GroqCache._generate_hash(prompt, lang, model)
        
        async with db.connection() as conn:
            query = """
            SELECT response, expires_at
            FROM groq_cache
            WHERE hash = $1 AND expires_at > NOW()
            """
            row = await conn.fetchrow(query, hash_key)
            
            if row:
                logger.debug(f"Cache hit for key: {hash_key}, type: {cache_type}")
                return row['response']
            
            logger.debug(f"Cache miss for key: {hash_key}, type: {cache_type}")
            return None

    @staticmethod
    async def set(prompt: str, response: str, lang: str, model: str, tokens_used: int, cache_type: str = 'recipe') -> bool:
        """Сохраняет результат в кэше с TTL"""
        
        ttl = GroqCache._get_ttl(cache_type)
        hash_key = GroqCache._generate_hash(prompt, lang, model)
        
        # --- ГЛАВНОЕ ИСПРАВЛЕНИЕ: Переносим арифметику времени в SQL ---
        # Передаем только NOW() в UTC и TTL как секунды.
        now_utc = datetime.now(timezone.utc)

        async with db.connection() as conn:
            query = """
            INSERT INTO groq_cache (hash, response, language, model, tokens_used, expires_at, created_at)
            -- expires_at рассчитывается в PostgreSQL: now_utc + TTL в секундах
            VALUES ($1, $2, $3, $4, $5, $7 + INTERVAL '1 second' * $6, $7)
            ON CONFLICT (hash) DO UPDATE
            SET response = EXCLUDED.response,
                tokens_used = EXCLUDED.tokens_used,
                expires_at = EXCLUDED.expires_at,
                created_at = EXCLUDED.created_at -- Обновляем created_at из EXCLUDED (что равно $7)
            """
            try:
                await conn.execute(
                    query, 
                    hash_key, 
                    response, 
                    lang, 
                    model, 
                    tokens_used, 
                    ttl,          # $6 - TTL (интервал в секундах)
                    now_utc       # $7 - Время создания (с UTC)
                )
                logger.debug(f"Cache set for key: {hash_key}, type: {cache_type}")
                return True
            except Exception as e:
                logger.error(f"Ошибка при сохранении кэша: {e}")
                logger.error(f"Тип now_utc: {type(now_utc)}, значение: {now_utc}, tzinfo: {now_utc.tzinfo}")
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
        """Получает статистику кэша"""
        async with db.connection() as conn:
            total_count = await conn.fetchval("SELECT COUNT(*) FROM groq_cache")
            expired_count = await conn.fetchval("SELECT COUNT(*) FROM groq_cache WHERE expires_at <= NOW()")
            
            # Проверка размера, безопасно для пустой таблицы
            size_val = await conn.fetchval("SELECT pg_relation_size('groq_cache')")
            size_kb = (size_val or 0) / 1024
            
            return {
                'total_entries': total_count or 0,
                'expired_entries': expired_count or 0,
                'current_entries': (total_count or 0) - (expired_count or 0),
                'estimated_size_kb': size_kb,
            }

groq_cache = GroqCache()