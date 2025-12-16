import logging
from typing import Optional, Dict, Any, Tuple
# ИСПРАВЛЕНО: Добавлен импорт 'date'
from datetime import datetime, timedelta, timezone, date

from . import db
from .models import UserBase, UserLanguage
from config import FREE_USER_LIMITS, PREMIUM_USER_LIMITS

logger = logging.getLogger(__name__)

class UserRepository:
    # ...
    
    @staticmethod
    async def _reset_daily_limits_if_needed(user_id: int) -> None:
        """Сбрасывает дневные лимиты, если наступил новый день"""
        async with db.connection() as conn:
            user = await conn.fetchrow(
                "SELECT last_reset_date FROM users WHERE user_id = $1", 
                user_id
            )

            if user:
                # ИСПРАВЛЕНО: Теперь 'date' импортирован
                today = date.today()
                last_reset = user['last_reset_date']

                if last_reset != today:
                    await conn.execute(
                        """
                        UPDATE users 
                        SET requests_today = 0, 
                            voice_requests_today = 0,
                            last_reset_date = $1
                        WHERE user_id = $2
                        """,
                        today, user_id
                    )
                    logger.info(f"Сброшены лимиты для пользователя {user_id}")
    # ... (все остальные методы)
    
    @staticmethod
    async def activate_premium(user_id: int, days: int = 30) -> bool:
        """Активирует премиум на указанное количество дней"""
        async with db.connection() as conn:
            # Правильно использует timezone.utc
            premium_until = datetime.now(timezone.utc) + timedelta(days=days) 

            result = await conn.execute(
                """
                UPDATE users 
                SET is_premium = TRUE,
                    premium_until = $1
                WHERE user_id = $2
                """,
                premium_until, user_id
            )

            return result is not None

# ... (остальные методы)

users_repo = UserRepository()