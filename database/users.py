import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta, timezone 
from . import db
from config import FREE_USER_LIMITS, PREMIUM_USER_LIMITS, TRIAL_DURATION_DAYS

logger = logging.getLogger(__name__)

class UserRepository:
    # ... (reset_daily_limits, check_and_increment_request - БЕЗ ИЗМЕНЕНИЙ) ...
    
    # ... (get_usage_stats, activate_premium, deactivate, check_expiry, get_or_create, get_user, update_language - БЕЗ ИЗМЕНЕНИЙ) ...

    # !!! НОВЫЙ МЕТОД !!!
    @staticmethod
    async def process_trial_activations() -> list[int]:
        """Активирует триал пользователям, зарегистрированным 48+ часов назад"""
        async with db.connection() as conn:
            users = await conn.fetch(
                """
                SELECT user_id FROM users 
                WHERE trial_status = 'pending' 
                  AND created_at < NOW() - INTERVAL '48 hours'
                  AND is_premium = FALSE
                """
            )
            
            activated_ids = []
            for row in users:
                uid = row['user_id']
                premium_until = datetime.now(timezone.utc) + timedelta(days=TRIAL_DURATION_DAYS)
                
                await conn.execute(
                    """
                    UPDATE users 
                    SET is_premium = TRUE, 
                        premium_until = $1,
                        trial_status = 'active'
                    WHERE user_id = $2
                    """,
                    premium_until, uid
                )
                activated_ids.append(uid)
                
            return activated_ids
    
    # ... (update_activity, count_users - БЕЗ ИЗМЕНЕНИЙ) ...

users_repo = UserRepository()