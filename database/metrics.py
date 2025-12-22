import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from . import db

logger = logging.getLogger(__name__)

class MetricsRepository:
    """Репозиторий для записи событий и метрик"""
    
    async def track_event(self, user_id: int, event_name: str, data: Dict[str, Any] = None) -> None:
        """Записывает событие в таблицу метрик"""
        
        data_to_store = data or {}

        try:
            # !!! ИСПРАВЛЕНИЕ: ПРЕВРАЩАЕМ DICT В СТРОКУ JSON !!!
            # Это решает проблему "expected str, got dict", если БД настроена как TEXT
            # И работает для JSONB тоже (Postgres сам распарсит строку)
            data_json_str = json.dumps(data_to_store, default=str)

            async with db.connection() as conn:
                query = """
                INSERT INTO metrics (user_id, event_name, data, created_at)
                VALUES ($1, $2, $3, $4)
                """
                await conn.execute(
                    query, 
                    user_id, 
                    event_name, 
                    data_json_str, # Отправляем строку!
                    datetime.now(timezone.utc)
                )
        except Exception as e:
            logger.critical(f"💀 КРИТИЧЕСКАЯ ОШИБКА записи метрики в БД ({event_name}): {e}", exc_info=True)


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

metrics = MetricsRepository()
