import logging
import json
from typing import Dict, List, Optional
from groq import AsyncGroq 

from config import GROQ_API_KEY, GROQ_MODEL, GROQ_MAX_TOKENS
from database.cache import groq_cache
from database.metrics import metrics
from locales.prompts import get_prompt 

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        if not GROQ_API_KEY:
            logger.warning("Groq API ключ не установлен.")
            self.client = None
        else:
            self.client = AsyncGroq(api_key=GROQ_API_KEY)

    async def _send_request(self, system_prompt: str, user_prompt: str, 
                            temperature: float = 0.5, cache_type: str = "general", lang: str = "ru", user_id: int = 0) -> str:
        if not self.client: return ""
        try:
            cache_key = groq_cache._generate_hash(f"{system_prompt[:100]}_{user_prompt[:200]}", lang, GROQ_MODEL)
            cached = await groq_cache.get(cache_key, lang, GROQ_MODEL, cache_type)
            if cached: return cached

            is_json = cache_type in ["analysis", "dish_list"]
            completion = await self.client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                model=GROQ_MODEL,
                temperature=temperature,
                max_tokens=GROQ_MAX_TOKENS,
                response_format={"type": "json_object"} if is_json else None
            )
            res = completion.choices[0].message.content
            await groq_cache.set(cache_key, res, lang, GROQ_MODEL, completion.usage.total_tokens, cache_type)
            return res
        except Exception as e:
            logger.error(f"Groq Error: {e}")
            return ""

    async def analyze_products(self, products: str, lang: str = "ru", user_id: int = 0) -> Optional[List[str]]:
        system = get_prompt(lang, "category_analysis")
        user = get_prompt(lang, "category_analysis_user").format(products=products)
        res = await self._send_request(system, user, 0.1, "analysis", lang, user_id)
        if not res: return None
        try:
            data = json.loads(res)
            return [k for k, v in data.items() if v is True] if isinstance(data, dict) else data
        except: return None

    # ИСПРАВЛЕНО: Название метода теперь совпадает с вызовом в recipes.py
    async def generate_dishes_from_products(self, products: str, category: str, lang: str = "ru", user_id: int = 0) -> List[dict]:
        system = get_prompt(lang, "dish_list_generation")
        user = get_prompt(lang, "dish_list_user").format(products=products, category=category)
        res = await self._send_request(system, user, 0.7, "dish_list", lang, user_id)
        if not res: return []
        try:
            data = json.loads(res)
            return data.get("dishes", []) if isinstance(data, dict) else data
        except: return []
! 
    async def generate_recipe(self, dish_name: str, products: str, lang: str = "ru", user_id: int = 0) -> str:
        system = get_prompt(lang, "recipe_generation")
        user = get_prompt(lang, "recipe_user").format(dish_name=dish_name, products=products)
        return await self._send_request(system, user, 0.7, "recipe", lang, user_id)

groq_service = GroqService()