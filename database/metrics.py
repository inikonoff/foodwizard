import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from . import db

logger = logging.getLogger(__name__)

class MetricsRepository:
    """Репозиторий для записи событий и метрик"""
    
    # 1. track_event - ЗАЩИЩАЕМ НА УРОВНЕ РЕПОЗИТОРИЯ
    async def track_event(self, user_id: int, event_name: str, data: Dict[str, Any] = None) -> None:
        """Записывает событие в таблицу метрик"""
        
        # Если data = None, используем пустой словарь
        data_to_store = data or {}

        # ИСПОЛЬЗУЕМ try/except ДЛЯ ЗАЩИТЫ БИЗНЕС-ЛОГИКИ
        try:
            async with db.connection() as conn:
                query = """
                INSERT INTO metrics (user_id, event_name, data, created_at)
                VALUES ($1, $2, $3, $4)
                """
                await conn.execute(
                    query, 
                    user_id, 
                    event_name, 
                    data_to_store, # Должно быть JSONB в БД
                    datetime.now(timezone.utc)
                )
        except Exception as e:
            # Логируем ошибку, но не бросаем ее выше
            logger.critical(f"💀 КРИТИЧЕСКАЯ ОШИБКА записи метрики в БД ({event_name}): {e}", exc_info=True)


    # 2. cleanup_old_metrics - ОСТАВЛЕН БЕЗ ИЗМЕНЕНИЙ (он надежен)
    async def cleanup_old_metrics(self, days_to_keep: int = 90) -> int:
        """Удаляет старые метрики"""
        try:
            async with db.connection() as conn:
                query = f"""
                DELETE FROM metrics 
                WHERE created_at < NOW() - interval '{days_to_keep} days'
                """
                result = await conn.execute(query)
                if result and "DELETE" in result:
                    count_str = result.split(" ")[1]
                    return int(count_str)
                return 0
        except Exception as e:
            logger.error(f"Ошибка при очистке метрик: {e}", exc_info=True)
            return 0

# Создаём глобальный экземпляр
metrics = MetricsRepository()