import logging
import hashlib
import json
from typing import Optional, Any
from datetime import datetime, timedelta
from . import db
from config import CACHE_TTL_RECIPE, CACHE_TTL_ANALYSIS, CACHE_TTL_VALIDATION

logger = logging.getLogger(__name__)

class GroqCache:
    @staticmethod
    def _generate_hash(prompt: str, lang: str, model: str) -> str:
        """ƒ¥­¥à¨àã¥â ã­¨ª «ì­ë© å¥è ¤«ï § ¯à®á """
        data = f"{prompt}_{lang}_{model}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def _get_ttl(cache_type: str) -> int:
        """‚®§¢à é ¥â TTL ¢ á¥ªã­¤ å ¢ § ¢¨á¨¬®áâ¨ ®â â¨¯  § ¯à®á """
        ttl_map = {
            'recipe': CACHE_TTL_RECIPE,
            'analysis': CACHE_TTL_ANALYSIS,
            'validation': CACHE_TTL_VALIDATION
        }
        return ttl_map.get(cache_type, CACHE_TTL_RECIPE)
    
    @staticmethod
    async def get(prompt: str, lang: str, model: str, cache_type: str = 'recipe') -> Optional[str]:
        """®«ãç ¥â à¥§ã«ìâ â ¨§ ªíè , ¥á«¨ ®­ ¥áâì ¨ ­¥ ¨áâñª"""
        async with db.connection() as conn:
            hash_key = GroqCache._generate_hash(prompt, lang, model)
            
            query = """
            SELECT response, expires_at 
            FROM groq_cache 
            WHERE hash = $1 AND expires_at > NOW()
            """
            
            row = await conn.fetchrow(query, hash_key)
            
            if row:
                logger.info(f"Šíè ¯®¯ ¤ ­¨¥ ¤«ï {hash_key[:8]}...")
                return row['response']
            else:
                logger.info(f"Šíè ¯à®¬ å ¤«ï {hash_key[:8]}...")
                return None
    
    @staticmethod
    async def set(prompt: str, lang: str, model: str, response: str, 
                  cache_type: str = 'recipe', tokens_used: Optional[int] = None) -> bool:
        """‘®åà ­ï¥â à¥§ã«ìâ â ¢ ªíè"""
        async with db.connection() as conn:
            hash_key = GroqCache._generate_hash(prompt, lang, model)
            ttl_seconds = GroqCache._get_ttl(cache_type)
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            
            query = """
            INSERT INTO groq_cache (hash, response, language, model, tokens_used, created_at, expires_at)
            VALUES ($1, $2, $3, $4, $5, NOW(), $6)
            ON CONFLICT (hash) DO UPDATE 
            SET response = EXCLUDED.response,
                language = EXCLUDED.language,
                model = EXCLUDED.model,
                tokens_used = EXCLUDED.tokens_used,
                created_at = NOW(),
                expires_at = EXCLUDED.expires_at
            """
            
            try:
                await conn.execute(
                    query,
                    hash_key,
                    response,
                    lang,
                    model,
                    tokens_used,
                    expires_at
                )
                logger.info(f"Šíè á®åà ­ñ­: {hash_key[:8]}... (TTL: {ttl_seconds} á¥ª)")
                return True
            except Exception as e:
                logger.error(f"Žè¨¡ª  á®åà ­¥­¨ï ¢ ªíè: {e}")
                return False
    
    @staticmethod
    async def clear_expired() -> int:
        """Žç¨é ¥â ¯à®áà®ç¥­­ë¥ § ¯¨á¨ ¨§ ªíè  ¨ ¢®§¢à é ¥â ª®«¨ç¥áâ¢® ã¤ «ñ­­ëå"""
        async with db.connection() as conn:
            query = "DELETE FROM groq_cache WHERE expires_at <= NOW() RETURNING hash"
            rows = await conn.fetch(query)
            logger.info(f"Žç¨é¥­® {len(rows)} ¯à®áà®ç¥­­ëå § ¯¨á¥© ªíè ")
            return len(rows)
    
    @staticmethod
    async def get_stats() -> Dict[str, Any]:
        """‚®§¢à é ¥â áâ â¨áâ¨ªã ªíè """
        async with db.connection() as conn:
            stats_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as active,
                COUNT(CASE WHEN expires_at <= NOW() THEN 1 END) as expired,
                AVG(LENGTH(response)) as avg_response_size,
                SUM(tokens_used) as total_tokens
            FROM groq_cache
            """
            
            row = await conn.fetchrow(stats_query)
            
            return {
                'total_entries': row['total'] or 0,
                'active_entries': row['active'] or 0,
                'expired_entries': row['expired'] or 0,
                'avg_response_size': round(row['avg_response_size'] or 0, 2),
                'total_tokens_saved': row['total_tokens'] or 0
            }

# ‘®§¤ ñ¬ íª§¥¬¯«ïà ¤«ï ã¤®¡­®£® ¨¬¯®àâ 
groq_cache = GroqCache()
