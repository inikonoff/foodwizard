import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from . import db

logger = logging.getLogger(__name__)

class MetricsCollector:
    @staticmethod
    async def track_event(user_id: int, event_type: str, details: Optional[Dict[str, Any]] = None):
        """‡ ¯¨áë¢ ¥â á®¡ëâ¨¥ ¢ ¬¥âà¨ª¨"""
        async with db.connection() as conn:
            query = """
            INSERT INTO metrics (user_id, event_type, details, created_at)
            VALUES ($1, $2, $3, NOW())
            """
            
            try:
                details_json = json.dumps(details) if details else '{}'
                await conn.execute(query, user_id, event_type, details_json)
            except Exception as e:
                logger.error(f"Žè¨¡ª  § ¯¨á¨ ¬¥âà¨ª¨: {e}")
    
    @staticmethod
    async def track_recipe_generated(user_id: int, dish_name: str, lang: str, 
                                     category: str, ingredients_count: int, cache_hit: bool):
        """‘¯¥æ¨ «ì­ë© ¬¥â®¤ ¤«ï ®âá«¥¦¨¢ ­¨ï £¥­¥à æ¨¨ à¥æ¥¯â """
        await MetricsCollector.track_event(
            user_id,
            'recipe_generated',
            {
                'dish_name': dish_name,
                'language': lang,
                'category': category,
                'ingredients_count': ingredients_count,
                'cache_hit': cache_hit
            }
        )
    
    @staticmethod
    async def track_favorite_added(user_id: int, dish_name: str, lang: str):
        """Žâá«¥¦¨¢ ¥â ¤®¡ ¢«¥­¨¥ ¢ ¨§¡à ­­®¥"""
        await MetricsCollector.track_event(
            user_id,
            'favorite_added',
            {
                'dish_name': dish_name,
                'language': lang
            }
        )
    
    @staticmethod
    async def track_voice_processed(user_id: int, success: bool, lang: str):
        """Žâá«¥¦¨¢ ¥â ®¡à ¡®âªã £®«®á®¢®£® á®®¡é¥­¨ï"""
        await MetricsCollector.track_event(
            user_id,
            'voice_processed',
            {
                'success': success,
                'language': lang
            }
        )
    
    @staticmethod
    async def get_daily_stats(date: Optional[datetime] = None) -> Dict[str, Any]:
        """‚®§¢à é ¥â áâ â¨áâ¨ªã §  ¤¥­ì"""
        if date is None:
            date = datetime.now()
        
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        async with db.connection() as conn:
            stats_query = """
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(CASE WHEN event_type = 'recipe_generated' THEN 1 END) as recipes_generated,
                COUNT(CASE WHEN event_type = 'favorite_added' THEN 1 END) as favorites_added,
                COUNT(CASE WHEN event_type = 'voice_processed' THEN 1 END) as voice_processed
            FROM metrics
            WHERE created_at >= $1 AND created_at < $2
            """
            
            row = await conn.fetchrow(stats_query, start_date, end_date)
            
            if row:
                return {
                    'date': start_date.date().isoformat(),
                    'total_events': row['total_events'] or 0,
                    'unique_users': row['unique_users'] or 0,
                    'recipes_generated': row['recipes_generated'] or 0,
                    'favorites_added': row['favorites_added'] or 0,
                    'voice_processed': row['voice_processed'] or 0
                }
            return {}
    
    @staticmethod
    async def get_language_stats(days: int = 7) -> Dict[str, Any]:
        """‚®§¢à é ¥â áâ â¨áâ¨ªã ¯® ï§ëª ¬ §  ¯®á«¥¤­¨¥ N ¤­¥©"""
        start_date = datetime.now() - timedelta(days=days)
        
        async with db.connection() as conn:
            # ‘â â¨áâ¨ª  ¯® ï§ëª ¬ ¤«ï à¥æ¥¯â®¢
            lang_query = """
            SELECT 
                details->>'language' as language,
                COUNT(*) as count
            FROM metrics
            WHERE event_type = 'recipe_generated' 
                AND created_at >= $1
                AND details->>'language' IS NOT NULL
            GROUP BY details->>'language'
            ORDER BY count DESC
            """
            
            rows = await conn.fetch(lang_query, start_date)
            
            languages = {}
            for row in rows:
                if row['language']:
                    languages[row['language']] = row['count']
            
            # ®¯ã«ïà­ë¥ ª â¥£®à¨¨
            category_query = """
            SELECT 
                details->>'category' as category,
                COUNT(*) as count
            FROM metrics
            WHERE event_type = 'recipe_generated' 
                AND created_at >= $1
                AND details->>'category' IS NOT NULL
            GROUP BY details->>'category'
            ORDER BY count DESC
            LIMIT 10
            """
            
            category_rows = await conn.fetch(category_query, start_date)
            
            categories = {}
            for row in category_rows:
                if row['category']:
                    categories[row['category']] = row['count']
            
            return {
                'period_days': days,
                'languages': languages,
                'categories': categories
            }
    
    @staticmethod
    async def cleanup_old_metrics(days_to_keep: int = 30) -> int:
        """“¤ «ï¥â áâ àë¥ ¬¥âà¨ª¨, ®áâ ¢«ïï â®«ìª® §  ¯®á«¥¤­¨¥ N ¤­¥©"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        async with db.connection() as conn:
            query = "DELETE FROM metrics WHERE created_at < $1 RETURNING id"
            rows = await conn.fetch(query, cutoff_date)
            
            logger.info(f"“¤ «¥­® {len(rows)} áâ àëå § ¯¨á¥© ¬¥âà¨ª")
            return len(rows)

# ‘®§¤ ñ¬ íª§¥¬¯«ïà ¤«ï ã¤®¡­®£® ¨¬¯®àâ 
metrics = MetricsCollector()
