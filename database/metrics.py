import logging
from typing import Dict, Any
from datetime import datetime, timedelta, timezone 

from . import db

logger = logging.getLogger(__name__)

class MetricsRepository:
    """Репозиторий для хранения и получения метрик использования"""

    @staticmethod
    async def track_event(user_id: int, event_name: str, metadata: Dict[str, Any] = None) -> None:
        """
        Отслеживает не-LLM событие (например, старт, настройки) путем записи в таблицу usage_metrics.
        ИСПРАВЛЕНИЕ: Перенаправляем событие в track_request с нулевыми токенами.
        """
        model_name = f"command_{event_name}"
        logger.debug(f"Event tracked: {event_name} for user {user_id}. Using model_name: {model_name}")
        
        # Переиспользуем track_request для записи события
        await MetricsRepository.track_request(
            user_id=user_id,
            model_name=model_name,
            tokens_used=0,
            is_cache_hit=False # Событие не кэшируется
        )

    @staticmethod
    async def track_request(user_id: int, model_name: str, tokens_used: int, is_cache_hit: bool):
        """Регистрирует каждый запрос (включая команды, переданные через track_event)"""
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
            
            # Обработка NULL-значений
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
        Использует timezone.utc для создания "осведомленного" времени.
        """
        async with db.connection() as conn:
            # Используем timezone.utc
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

            query = "DELETE FROM usage_metrics WHERE timestamp < $1 RETURNING user_id"
            rows = await conn.fetch(query, cutoff_date)
            
            logger.info(f"Очищено {len(rows)} старых записей метрик (старше {days_to_keep} дней)")
            return len(rows)

metrics = MetricsRepository()
