import logging
from typing import Dict, Any
from datetime import datetime, timedelta, timezone # <-- ДОБАВЛЕН ИМПОРТ timezone

from . import db

logger = logging.getLogger(__name__)

class MetricsRepository:
    """Репозиторий для хранения и получения метрик использования"""

    @staticmethod
    async def track_request(user_id: int, model_name: str, tokens_used: int, is_cache_hit: bool):
        """Регистрирует каждый запрос"""
        async with db.connection() as conn:
            query = """
            INSERT INTO usage_metrics (user_id, model_name, tokens_used, is_cache_hit, timestamp)
            VALUES ($1, $2, $3, $4, NOW())
            """
            try:
                await conn.execute(
                    query, 
                    user_id, 
                    model_name, 
                    tokens_used, 
                    is_cache_hit
                )
            except Exception as e:
                logger.error(f"Ошибка при сохранении метрики для пользователя {user_id}: {e}")

    @staticmethod
    async def get_total_stats() -> Dict[str, Any]:
        """Возвращает общую статистику использования"""
        async with db.connection() as conn:
            query = """
            SELECT 
                COUNT(*) as total_requests,
                SUM(tokens_used) as total_tokens,
                SUM(CASE WHEN is_cache_hit = TRUE THEN 1 ELSE 0 END) as cache_hits,
                COUNT(*) - SUM(CASE WHEN is_cache_hit = TRUE THEN 1 ELSE 0 END) as non_cache_requests
            FROM usage_metrics
            """
            row = await conn.fetchrow(query)
            
            return {
                'total_requests': row['total_requests'] or 0,
                'total_tokens': row['total_tokens'] or 0,
                'cache_hits': row['cache_hits'] or 0,
                'non_cache_requests': row['non_cache_requests'] or 0,
            }

    @staticmethod
    async def cleanup_old_metrics(days_to_keep: int = 90) -> int:
        """
        Очищает метрики старше указанного количества дней.
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Используем timezone.utc для создания "осведомленного" времени.
        """
        async with db.connection() as conn:
            # ИСПРАВЛЕНО: Добавлен timezone.utc
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

            query = "DELETE FROM usage_metrics WHERE timestamp < $1 RETURNING user_id"
            rows = await conn.fetch(query, cutoff_date)
            
            logger.info(f"Очищено {len(rows)} старых записей метрик (старше {days_to_keep} дней)")
            return len(rows)

metrics = MetricsRepository()
