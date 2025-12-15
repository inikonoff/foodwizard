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
        """„®¡ ¢«ï¥â à¥æ¥¯â ¢ ¨§¡à ­­®¥"""
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
                row = await conn.fetchrow(
                    query,
                    favorite.user_id,
                    favorite.dish_name,
                    favorite.recipe_text,
                    favorite.category.value if favorite.category else None,
                    favorite.ingredients,
                    favorite.language.value
                )
                return row is not None
            except Exception as e:
                logger.error(f"Žè¨¡ª  ¯à¨ ¤®¡ ¢«¥­¨¨ ¢ ¨§¡à ­­®¥: {e}")
                return False
    
    @staticmethod
    async def remove_favorite(user_id: int, dish_name: str) -> bool:
        """“¤ «ï¥â à¥æ¥¯â ¨§ ¨§¡à ­­®£®"""
        async with db.connection() as conn:
            query = "DELETE FROM favorites WHERE user_id = $1 AND dish_name = $2"
            result = await conn.execute(query, user_id, dish_name)
            return "DELETE" in result
    
    @staticmethod
    async def get_favorites_page(user_id: int, page: int = 1) -> Tuple[List[Dict[str, Any]], int]:
        """®«ãç ¥â áâà ­¨æã ¨§¡à ­­ëå à¥æ¥¯â®¢ á ¯ £¨­ æ¨¥©"""
        async with db.connection() as conn:
            # ‘­ ç «  ¯®«ãç ¥¬ ®¡é¥¥ ª®«¨ç¥áâ¢®
            count_query = "SELECT COUNT(*) FROM favorites WHERE user_id = $1"
            total_count = await conn.fetchval(count_query, user_id)
            
            if total_count == 0:
                return [], 0
            
            #  ááç¨âë¢ ¥¬ ¯ £¨­ æ¨î
            offset = (page - 1) * FAVORITES_PER_PAGE
            total_pages = (total_count + FAVORITES_PER_PAGE - 1) // FAVORITES_PER_PAGE
            
            # ®«ãç ¥¬ à¥æ¥¯âë ¤«ï â¥ªãé¥© áâà ­¨æë
            data_query = """
            SELECT id, dish_name, recipe_text, category, ingredients, language, created_at
            FROM favorites 
            WHERE user_id = $1 
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """
            
            rows = await conn.fetch(data_query, user_id, FAVORITES_PER_PAGE, offset)
            
            favorites = []
            for row in rows:
                favorites.append({
                    'id': row['id'],
                    'dish_name': row['dish_name'],
                    'recipe_text': row['recipe_text'],
                    'category': row['category'],
                    'ingredients': row['ingredients'],
                    'language': row['language'],
                    'created_at': row['created_at']
                })
            
            return favorites, total_pages
    
    @staticmethod
    async def get_favorite(user_id: int, dish_name: str) -> Optional[Dict[str, Any]]:
        """®«ãç ¥â ª®­ªà¥â­ë© à¥æ¥¯â ¨§ ¨§¡à ­­®£®"""
        async with db.connection() as conn:
            query = """
            SELECT id, dish_name, recipe_text, category, ingredients, language, created_at
            FROM favorites 
            WHERE user_id = $1 AND dish_name = $2
            """
            
            row = await conn.fetchrow(query, user_id, dish_name)
            return dict(row) if row else None
    
    @staticmethod
    async def count_favorites(user_id: int) -> int:
        """‘ç¨â ¥â ª®«¨ç¥áâ¢® ¨§¡à ­­ëå à¥æ¥¯â®¢ ã ¯®«ì§®¢ â¥«ï"""
        async with db.connection() as conn:
            query = "SELECT COUNT(*) FROM favorites WHERE user_id = $1"
            return await conn.fetchval(query, user_id)
    
    @staticmethod
    async def is_favorite(user_id: int, dish_name: str) -> bool:
        """à®¢¥àï¥â, ¥áâì «¨ à¥æ¥¯â ¢ ¨§¡à ­­®¬"""
        async with db.connection() as conn:
            query = "SELECT 1 FROM favorites WHERE user_id = $1 AND dish_name = $2 LIMIT 1"
            row = await conn.fetchrow(query, user_id, dish_name)
            return row is not None
    
    @staticmethod
    async def get_all_favorites(user_id: int) -> List[Dict[str, Any]]:
        """®«ãç ¥â ¢á¥ ¨§¡à ­­ë¥ à¥æ¥¯âë ¯®«ì§®¢ â¥«ï (¡¥§ ¯ £¨­ æ¨¨)"""
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
        """Žç¨é ¥â ¢á¥ ¨§¡à ­­®¥ ¯®«ì§®¢ â¥«ï"""
        async with db.connection() as conn:
            query = "DELETE FROM favorites WHERE user_id = $1"
            result = await conn.execute(query, user_id)
            return "DELETE" in result

# ‘®§¤ ñ¬ íª§¥¬¯«ïà ¤«ï ã¤®¡­®£® ¨¬¯®àâ 
favorites_repo = FavoritesRepository()
