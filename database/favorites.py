import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from . import db
from .models import FavoriteRecipe, Category, UserLanguage
from config import FAVORITES_PER_PAGE

logger = logging.getLogger(__name__)

class FavoritesRepository:
    @staticmethod
    async def add_favorite(favorite: FavoriteRecipe) -> bool:
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
                # !!! БЕЗОПАСНОЕ ИЗВЛЕЧЕНИЕ ЗНАЧЕНИЙ !!!
                # Проверяем, есть ли атрибут .value (если это Enum) или используем как есть (если str)
                cat_val = favorite.category.value if hasattr(favorite.category, 'value') else favorite.category
                lang_val = favorite.language.value if hasattr(favorite.language, 'value') else favorite.language
                
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
                logger.error(f"Error add_favorite: {e}")
                return False
    
    @staticmethod
    async def remove_favorite(user_id: int, dish_name: str) -> bool:
        async with db.connection() as conn:
            query = "DELETE FROM favorites WHERE user_id = $1 AND dish_name = $2"
            result = await conn.execute(query, user_id, dish_name)
            return "DELETE" in result
    
    @staticmethod
    async def get_favorites_page(user_id: int, page: int = 1) -> Tuple[List[Dict[str, Any]], int]:
        async with db.connection() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM favorites WHERE user_id = $1", user_id)
            if count == 0: return [], 0
            
            offset = (page - 1) * FAVORITES_PER_PAGE
            total_pages = (count + FAVORITES_PER_PAGE - 1) // FAVORITES_PER_PAGE
            
            query = """
            SELECT id, dish_name, created_at
            FROM favorites 
            WHERE user_id = $1 
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """
            rows = await conn.fetch(query, user_id, FAVORITES_PER_PAGE, offset)
            return [dict(row) for row in rows], total_pages
    
    @staticmethod
    async def get_favorite_by_id(fav_id: int) -> Optional[Dict[str, Any]]:
        async with db.connection() as conn:
            query = "SELECT * FROM favorites WHERE id = $1"
            row = await conn.fetchrow(query, fav_id)
            return dict(row) if row else None
            
    @staticmethod
    async def is_favorite(user_id: int, dish_name: str) -> bool:
        async with db.connection() as conn:
            row = await conn.fetchrow("SELECT 1 FROM favorites WHERE user_id = $1 AND dish_name = $2 LIMIT 1", user_id, dish_name)
            return row is not None

    @staticmethod
    async def count_favorites(user_id: int) -> int:
        async with db.connection() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM favorites WHERE user_id = $1", user_id)

favorites_repo = FavoritesRepository()
