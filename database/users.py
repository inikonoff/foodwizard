import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta

from . import db
from .models import UserBase, UserLanguage
from config import FREE_USER_LIMITS, PREMIUM_USER_LIMITS

logger = logging.getLogger(__name__)

class UserRepository:
    """¥¯®§¨â®à¨© ¤«ï à ¡®âë á ¯®«ì§®¢ â¥«ï¬¨ á ¯®¤¤¥à¦ª®© «¨¬¨â®¢"""
    
    @staticmethod
    async def _reset_daily_limits_if_needed(user_id: int) -> None:
        """‘¡à áë¢ ¥â ¤­¥¢­ë¥ «¨¬¨âë, ¥á«¨ ­ áâã¯¨« ­®¢ë© ¤¥­ì"""
        async with db.connection() as conn:
            user = await conn.fetchrow(
                "SELECT last_reset_date FROM users WHERE user_id = $1", 
                user_id
            )
            
            if user:
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
                    logger.info(f"‘¡à®è¥­ë «¨¬¨âë ¤«ï ¯®«ì§®¢ â¥«ï {user_id}")
    
    @staticmethod
    async def check_and_increment_request(user_id: int, request_type: str = "text") -> Tuple[bool, int, int]:
        """
        à®¢¥àï¥â ¨ ã¢¥«¨ç¨¢ ¥â áç¥âç¨ª § ¯à®á®¢.
        ‚®§¢à é ¥â (à §à¥èñ­, ¨á¯®«ì§®¢ ­®, «¨¬¨â)
        """
        # ‘­ ç «  á¡à áë¢ ¥¬ «¨¬¨âë ¥á«¨ ­ã¦­®
        await UserRepository._reset_daily_limits_if_needed(user_id)
        
        async with db.connection() as conn:
            # «®ª¨àã¥¬ áâà®ªã ¤«ï  â®¬ à­®£® ®¡­®¢«¥­¨ï
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
            
            # ‚ë¡¨à ¥¬ «¨¬¨âë ¢ § ¢¨á¨¬®áâ¨ ®â â¨¯  ¯®«ì§®¢ â¥«ï
            if is_premium:
                limits = PREMIUM_USER_LIMITS
            else:
                limits = FREE_USER_LIMITS
            
            # ‚ë¡¨à ¥¬ ­ã¦­ë© áç¥âç¨ª ¨ «¨¬¨â
            if request_type == "voice":
                current_count = user['voice_requests_today']
                limit = limits['voice_per_day']
                update_field = "voice_requests_today"
            else:
                current_count = user['requests_today']
                limit = limits['daily_requests']
                update_field = "requests_today"
            
            # à®¢¥àï¥¬ «¨¬¨â
            if current_count >= limit:
                return False, current_count, limit
            
            # “¢¥«¨ç¨¢ ¥¬ áç¥âç¨ª
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
        """‚®§¢à é ¥â áâ â¨áâ¨ªã ¨á¯®«ì§®¢ ­¨ï"""
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
            
            # Ž¯à¥¤¥«ï¥¬ «¨¬¨âë
            if row['is_premium']:
                limits = PREMIUM_USER_LIMITS
            else:
                limits = FREE_USER_LIMITS
            
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
        """€ªâ¨¢¨àã¥â ¯à¥¬¨ã¬ ­  ãª § ­­®¥ ª®«¨ç¥áâ¢® ¤­¥©"""
        async with db.connection() as conn:
            premium_until = datetime.now() + timedelta(days=days)
            
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
    
    @staticmethod
    async def deactivate_premium(user_id: int) -> bool:
        """„¥ ªâ¨¢¨àã¥â ¯à¥¬¨ã¬"""
        async with db.connection() as conn:
            result = await conn.execute(
                """
                UPDATE users 
                SET is_premium = FALSE,
                    premium_until = NULL
                WHERE user_id = $1
                """,
                user_id
            )
            
            return result is not None
    
    @staticmethod
    async def check_premium_expiry() -> int:
        """à®¢¥àï¥â ¨áâ¥ç¥­¨¥ áà®ª  ¯à¥¬¨ã¬ , ¢®§¢à é ¥â ª®«¨ç¥áâ¢® ¤¥ ªâ¨¢¨à®¢ ­­ëå"""
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
            
            # ˆ§¢«¥ª ¥¬ ª®«¨ç¥áâ¢® ®¡­®¢«¥­­ëå áâà®ª
            if result and "UPDATE" in result:
                count_str = result.split(" ")[1]
                return int(count_str)
            return 0
    
    @staticmethod
    async def get_or_create(user_id: int, first_name: str, 
                           username: Optional[str] = None, 
                           language: UserLanguage = UserLanguage.RU) -> Dict[str, Any]:
        """®«ãç ¥â ¨«¨ á®§¤ ñâ ¯®«ì§®¢ â¥«ï (®¡­®¢«ñ­­ ï ¢¥àá¨ï)"""
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
            RETURNING 
                user_id, first_name, username, language_code, 
                is_premium, premium_until, created_at, 
                last_active_at, last_reset_date,
                requests_today, voice_requests_today, total_requests
            """
            
            try:
                row = await conn.fetchrow(
                    query, 
                    user_id, 
                    first_name, 
                    username, 
                    language.value
                )
                if row:
                    return dict(row)
            except Exception as e:
                logger.error(f"Žè¨¡ª  ¯à¨ á®§¤ ­¨¨ ¯®«ì§®¢ â¥«ï {user_id}: {e}")
                raise
        
        return {}
    
    @staticmethod
    async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
        """®«ãç ¥â ¤ ­­ë¥ ¯®«ì§®¢ â¥«ï"""
        async with db.connection() as conn:
            query = """
            SELECT user_id, first_name, username, language_code, is_premium, 
                   premium_until, created_at, last_active_at, last_reset_date,
                   requests_today, voice_requests_today, total_requests
            FROM users 
            WHERE user_id = $1
            """
            
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else None
    
    @staticmethod
    async def update_language(user_id: int, language: UserLanguage) -> bool:
        """Ž¡­®¢«ï¥â ï§ëª ¯®«ì§®¢ â¥«ï"""
        async with db.connection() as conn:
            query = "UPDATE users SET language_code = $1 WHERE user_id = $2"
            result = await conn.execute(query, language.value, user_id)
            return result is not None
    
    @staticmethod
    async def set_premium(user_id: int, is_premium: bool = True) -> bool:
        """“áâ ­ ¢«¨¢ ¥â ¯à¥¬¨ã¬ áâ âãá"""
        async with db.connection() as conn:
            query = "UPDATE users SET is_premium = $1 WHERE user_id = $2"
            result = await conn.execute(query, is_premium, user_id)
            return result is not None
    
    @staticmethod
    async def update_activity(user_id: int) -> None:
        """Ž¡­®¢«ï¥â ¢à¥¬ï ¯®á«¥¤­¥©  ªâ¨¢­®áâ¨"""
        async with db.connection() as conn:
            query = "UPDATE users SET last_active_at = NOW() WHERE user_id = $1"
            await conn.execute(query, user_id)
    
    @staticmethod
    async def get_all_users(limit: int = 1000) -> list:
        """®«ãç ¥â ¢á¥å ¯®«ì§®¢ â¥«¥© (¤«ï  ¤¬¨­¨áâà â®à )"""
        async with db.connection() as conn:
            query = "SELECT * FROM users ORDER BY last_active_at DESC LIMIT $1"
            rows = await conn.fetch(query, limit)
            return [dict(row) for row in rows]
    
    @staticmethod
    async def count_users() -> int:
        """‘ç¨â ¥â ®¡é¥¥ ª®«¨ç¥áâ¢® ¯®«ì§®¢ â¥«¥©"""
        async with db.connection() as conn:
            query = "SELECT COUNT(*) FROM users"
            return await conn.fetchval(query)

# ‘®§¤ ñ¬ £«®¡ «ì­ë© íª§¥¬¯«ïà ¤«ï ¨¬¯®àâ 
users_repo = UserRepository()
