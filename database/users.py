import logging
from typing import Optional, Dict, Any, Tuple
# ИСПРАВЛЕНИЕ: Добавлен импорт 'date'
from datetime import datetime, timedelta, timezone, date

from . import db
from .models import UserBase, UserLanguage
from config import FREE_USER_LIMITS, PREMIUM_USER_LIMITS

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
                # ИСПРАВЛЕНИЕ: Теперь 'date' импортирован
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

    @staticmethod
    async def check_and_increment_request(user_id: int, request_type: str = "text") -> Tuple[bool, int, int]:
        """
        Проверяет и увеличивает счетчик запросов.
        Возвращает (разрешён, использовано, лимит)
        """
        # Сначала сбрасываем лимиты если нужно
        await UserRepository._reset_daily_limits_if_needed(user_id)

        async with db.connection() as conn:
            # Блокируем строку для атомарного обновления
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

            # Выбираем лимиты в зависимости от типа пользователя
            if is_premium:
                limits = PREMIUM_USER_LIMITS
            else:
                limits = FREE_USER_LIMITS

            # Выбираем нужный счетчик и лимит
            if request_type == "voice":
                current_count = user['voice_requests_today']
                limit = limits['voice_per_day']
                update_field = "voice_requests_today"
            else:
                current_count = user['requests_today']
                limit = limits['daily_requests']
                update_field = "requests_today"

            # Проверяем лимит
            if current_count >= limit:
                return False, current_count, limit

            # Увеличиваем счетчик
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

            # Определяем лимиты
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

    @staticmethod
    async def deactivate_premium(user_id: int) -> bool:
        """Деактивирует премиум"""
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
        """Проверяет истечение срока премиума, возвращает количество деактивированных"""
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

            # Извлекаем количество обновленных строк
            if result and "UPDATE" in result:
                count_str = result.split(" ")[1]
                return int(count_str)
            return 0

    @staticmethod
    async def get_or_create(user_id: int, first_name: str, 
                           username: Optional[str] = None, 
                           language: UserLanguage = UserLanguage.RU) -> Dict[str, Any]:
        """Получает или создаёт пользователя (обновлённая версия)"""
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
                logger.error(f"Ошибка при создании пользователя {user_id}: {e}")
                raise

        return {}

    @staticmethod
    async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
        """Получает данные пользователя"""
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
        """Обновляет язык пользователя"""
        async with db.connection() as conn:
            query = "UPDATE users SET language_code = $1 WHERE user_id = $2"
            result = await conn.execute(query, language.value, user_id)
            return result is not None

    @staticmethod
    async def set_premium(user_id: int, is_premium: bool = True) -> bool:
        """Устанавливает премиум статус"""
        async with db.connection() as conn:
            query = "UPDATE users SET is_premium = $1 WHERE user_id = $2"
            result = await conn.execute(query, is_premium, user_id)
            return result is not None

    @staticmethod
    async def update_activity(user_id: int) -> None:
        """Обновляет время последней активности"""
        async with db.connection() as conn:
            query = "UPDATE users SET last_active_at = NOW() WHERE user_id = $1"
            await conn.execute(query, user_id)

    @staticmethod
    async def get_all_users(limit: int = 1000) -> list:
        """Получает всех пользователей (для администратора)"""
        async with db.connection() as conn:
            query = "SELECT * FROM users ORDER BY last_active_at DESC LIMIT $1"
            rows = await conn.fetch(query, limit)
            return [dict(row) for row in rows]

    @staticmethod
    async def count_users() -> int:
        """Считает общее количество пользователей"""
        async with db.connection() as conn:
            query = "SELECT COUNT(*) FROM users"
            return await conn.fetchval(query)

# Создаём глобальный экземпляр для импорта
users_repo = UserRepository()
