import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from . import db
# Импорт моделей только для аннотации типов
from .models import FavoriteRecipe
from config import FAVORITES_PER_PAGE

logger = logging.getLogger(__name__)

class FavoritesRepository:
    @staticmethod
    async def add_favorite(favorite: FavoriteRecipe) -> bool:
        """Добавляет рецепт в избранное"""
        async with db.connection() as conn:
            query = """
            INSERT INTO favorites (user_id, dish_name, recipe_text, category, ingredients, language, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            ON CONFLICT (user_id, dish_name) DO UPDATE 
            SET recipe_text = EXCLUDED.recipe_text,
                category = EXCLUDED.category,
                ingredients = EXCLUDED.ingredients,
                language = EXCLUDED.language,
                created_at = NOW()
            RETURNING id
            """
            
            try:
                # !!! КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ (Safeguard) !!!
                # Проверяем: это Enum (есть .value) или уже просто строка?
                # Это предотвращает ошибку "'str' object has no attribute 'value'"
                
                # Обработка категории
                if favorite.category and hasattr(favorite.category, 'value'):
                    cat_val = favorite.category.value
                else:
                    cat_val = favorite.category # Это уже строка или None

                # Обработка языка
                if favorite.language and hasattr(favorite.language, 'value'):
                    lang_val = favorite.language.value
                else:
                    lang_val = favorite.language # Это уже строка

                row = await conn.fetchrow(
                    query,
                    favorite.user_id,
                    favorite.dish_name,
                    favorite.recipe_text,
                    cat_val,
                    favorite.ingredients,
                    lang_val
                )
                return row is not None
            except Exception as e:
                logger.error(f"Ошибка при добавлении в избранное (add_favorite): {e}", exc_info=True)
                return False
    
    @staticmethod
    async def remove_favorite(user_id: int, dish_name: str) -> bool:
        """Удаляет рецепт из избранного"""
        async with db.connection() as conn:
            query = "DELETE FROM favorites WHERE user_id = $1 AND dish_name = $2"
            result = await conn.execute(query, user_id, dish_name)
            return "DELETE" in result
    
    @staticmethod
    async def get_favorites_page(user_id: int, page: int = 1) -> Tuple[List[Dict[str, Any]], int]:
        """Получает страницу избранных рецептов с пагинацией"""
        async with db.connection() as conn:
            # Сначала получаем общее количество
            count_query = "SELECT COUNT(*) FROM favorites WHERE user_id = $1"
            total_count = await conn.fetchval(count_query, user_id)
            
            if total_count == 0:
                return [], 0
            
            # Рассчитываем пагинацию
            offset = (page - 1) * FAVORITES_PER_PAGE
            total_pages = (total_count + FAVORITES_PER_PAGE - 1) // FAVORITES_PER_PAGE
            
            # Получаем рецепты для текущей страницы
            data_query = """
            SELECT id, dish_name, created_at, language
            FROM favorites 
            WHERE user_id = $1 
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """
            
            rows = await conn.fetch(data_query, user_id, FAVORITES_PER_PAGE, offset)
            return [dict(row) for row in rows], total_pages
    
    @staticmethod
    async def get_favorite_by_id(fav_id: int) -> Optional[Dict[str, Any]]:
        """Получает рецепт по ID"""
        async with db.connection() as conn:
            query = """
            SELECT id, dish_name, recipe_text, category, ingredients, language, created_at
            FROM favorites 
            WHERE id = $1
            """
            
            row = await conn.fetchrow(query, fav_id)
            return dict(row) if row else None
            
    @staticmethod
    async def is_favorite(user_id: int, dish_name: str) -> bool:
        """Проверяет, есть ли рецепт в избранном"""
        async with db.connection() as conn:
            query = "SELECT 1 FROM favorites WHERE user_id = $1 AND dish_name = $2 LIMIT 1"
            row = await conn.fetchrow(query, user_id, dish_name)
            return row is not None

    @staticmethod
    async def count_favorites(user_id: int) -> int:
        """Считает количество избранных рецептов"""
        async with db.connection() as conn:
            query = "SELECT COUNT(*) FROM favorites WHERE user_id = $1"
            return await conn.fetchval(query, user_id)
    
    @staticmethod
    async def get_all_favorites(user_id: int) -> List[Dict[str, Any]]:
        """Получает все избранные рецепты (для бэкапа или API)"""
        async with db.connection() as conn:
            query = """
            SELECT id, dish_name, recipe_text, category, ingredients, language, created_at
            FROM favorites 
            WHERE user_id = $1 
            ORDER BY created_at DESC
            """
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]
    
    @staticmethod
    async def clear_favorites(user_id: int) -> bool:
        """Очищает всё избранное"""
        async with db.connection() as conn:
            query = "DELETE FROM favorites WHERE user_id = $1"
            result = await conn.execute(query, user_id)
            return "DELETE" in result

# Создаём экземпляр
favorites_repo = FavoritesRepository()