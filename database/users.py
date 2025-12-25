import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta, timezone 
from . import db
from .models import UserBase, UserLanguage 
from config import FREE_USER_LIMITS, PREMIUM_USER_LIMITS, TRIAL_DURATION_DAYS

logger = logging.getLogger(__name__)

class UserRepository:
    """Репозиторий для работы с пользователями с поддержкой лимитов"""
    
    @staticmethod
    async def _reset_daily_limits_if_needed(user_id: int) -> None:
        """Сбрасывает дневные лимиты, если наступил новый день"""
        async with db.connection() as conn:
            user = await conn.fetchrow(
                "SELECT last_reset_date FROM users WHERE user_id = $1", 
                user_id
            )
            
            if user:
                today = await conn.fetchval("SELECT CURRENT_DATE")
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
    
    @staticmethod
    async def check_and_increment_request(user_id: int, request_type: str = "text") -> Tuple[bool, int, int]:
        """Проверяет и увеличивает счетчик запросов."""
        await UserRepository._reset_daily_limits_if_needed(user_id)
        
        async with db.connection() as conn:
            user = await conn.fetchrow(
                """
                SELECT is_premium, requests_today, voice_requests_today 
                FROM users 
                WHERE user_id = $1
                FOR UPDATE
                """, 
                user_id
            )
            
            if not user:
                return False, 0, 0
            
            is_premium = user['is_premium']
            limits = PREMIUM_USER_LIMITS if is_premium else FREE_USER_LIMITS
            
            if request_type == "voice":
                current_count = user['voice_requests_today']
                limit = limits['voice_per_day']
                update_field = "voice_requests_today"
            else:
                current_count = user['requests_today']
                limit = limits['daily_requests']
                update_field = "requests_today"
            
            if current_count >= limit:
                return False, current_count, limit
            
            new_count = current_count + 1
            await conn.execute(
                f"""
                UPDATE users 
                SET {update_field} = $1, 
                    total_requests = total_requests + 1,
                    last_active_at = NOW()
                WHERE user_id = $2
                """,
                new_count, user_id
            )
            
            return True, new_count, limit
    
    @staticmethod
    async def get_usage_stats(user_id: int) -> Dict[str, Any]:
        """Возвращает статистику использования"""
        async with db.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    requests_today,
                    voice_requests_today,
                    total_requests,
                    is_premium,
                    premium_until,
                    last_reset_date
                FROM users 
                WHERE user_id = $1
                """,
                user_id
            )
            
            if not row:
                return {}
            
            limits = PREMIUM_USER_LIMITS if row['is_premium'] else FREE_USER_LIMITS
            
            return {
                'text_requests_used': row['requests_today'],
                'text_requests_limit': limits['daily_requests'],
                'voice_requests_used': row['voice_requests_today'],
                'voice_requests_limit': limits['voice_per_day'],
                'total_requests': row['total_requests'],
                'is_premium': row['is_premium'],
                'premium_until': row['premium_until'],
                'last_reset_date': row['last_reset_date'],
                'remaining_text': max(0, limits['daily_requests'] - row['requests_today']),
                'remaining_voice': max(0, limits['voice_per_day'] - row['voice_requests_today'])
            }
    
    @staticmethod
    async def activate_premium(user_id: int, days: int = 30) -> bool:
        """Активирует премиум"""
        async with db.connection() as conn:
            premium_until = datetime.now(timezone.utc) + timedelta(days=days)
            result = await conn.execute(
                "UPDATE users SET is_premium = TRUE, premium_until = $1 WHERE user_id = $2",
                premium_until, user_id
            )
            return result is not None
    
    @staticmethod
    async def deactivate_premium(user_id: int) -> bool:
        async with db.connection() as conn:
            result = await conn.execute(
                "UPDATE users SET is_premium = FALSE, premium_until = NULL WHERE user_id = $1",
                user_id
            )
            return result is not None

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
    
    @staticmethod
    async def check_premium_expiry() -> int:
        """Проверяет истечение срока премиума"""
        async with db.connection() as conn:
            result = await conn.execute(
                """
                UPDATE users 
                SET is_premium = FALSE,
                    premium_until = NULL
                WHERE is_premium = TRUE 
                  AND premium_until < CURRENT_DATE
                """
            )
            if result and "UPDATE" in result:
                return int(result.split(" ")[1])
            return 0
    
    @staticmethod
    async def get_or_create(user_id: int, first_name: str, 
                           username: Optional[str] = None, 
                           language: str = "en") -> Dict[str, Any]:
        """Получает или создаёт пользователя. Default lang = EN."""
        async with db.connection() as conn:
            query = """
            INSERT INTO users (
                user_id, first_name, username, language_code, 
                created_at, last_active_at, last_reset_date
            )
            VALUES ($1, $2, $3, $4, NOW(), NOW(), CURRENT_DATE)
            ON CONFLICT (user_id) DO UPDATE 
            SET first_name = EXCLUDED.first_name,
                username = EXCLUDED.username,
                last_active_at = NOW()
            RETURNING *
            """
            try:
                row = await conn.fetchrow(query, user_id, first_name, username, language)
                return dict(row) if row else {}
            except Exception as e:
                logger.error(f"Ошибка при создании пользователя {user_id}: {e}")
                raise
    
    @staticmethod
    async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
        async with db.connection() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            return dict(row) if row else None
    
    @staticmethod
    async def update_language(user_id: int, language: Any) -> bool:
        lang_val = language.value if hasattr(language, 'value') else str(language)
        async with db.connection() as conn:
            result = await conn.execute("UPDATE users SET language_code = $1 WHERE user_id = $2", lang_val, user_id)
            return result is not None
    
    @staticmethod
    async def update_activity(user_id: int) -> None:
        async with db.connection() as conn:
            await conn.execute("UPDATE users SET last_active_at = NOW() WHERE user_id = $1", user_id)
    
    @staticmethod
    async def get_all_users(limit: int = 1000) -> list:
        async with db.connection() as conn:
            rows = await conn.fetch("SELECT * FROM users ORDER BY last_active_at DESC LIMIT $1", limit)
            return [dict(row) for row in rows]
    
    @staticmethod
    async def count_users() -> int:
        async with db.connection() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM users")

users_repo = UserRepository()