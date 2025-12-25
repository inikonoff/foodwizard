import logging
import json
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone

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
            
    async def close(self):
        if self.client and hasattr(self.client, 'close'):
            await self.client.close()

    async def _send_request(self, system_prompt: str, user_prompt: str, 
                            temperature: float = 0.5, cache_type: str = "general", lang: str = "ru", user_id: int = 0) -> str:
        if not self.client: return "Error: API key missing."
        try:
            # В хэш добавляем system_prompt, так как он меняется для премиума (КБЖУ)
            cache_key = groq_cache._generate_hash(f"{system_prompt[:200]}_{user_prompt[:200]}", lang, GROQ_MODEL)
            cached_response = await groq_cache.get(prompt=cache_key, lang=lang, model=GROQ_MODEL, cache_type=cache_type)
            if cached_response:
                await metrics.track_event(user_id, "groq_cache_hit", {"key": cache_key})
                return cached_response

            is_json = cache_type in ["analysis", "validation", "intent", "dish_list"]
            
            chat_completion = await self.client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                model=GROQ_MODEL, temperature=temperature, max_tokens=GROQ_MAX_TOKENS,
                response_format={"type": "json_object"} if is_json else None,
                timeout=60.0
            )

            response_text = chat_completion.choices[0].message.content
            
            await groq_cache.set(prompt=cache_key, response=response_text, lang=lang, model=GROQ_MODEL, tokens_used=chat_completion.usage.total_tokens, cache_type=cache_type)
            await metrics.track_event(user_id, "groq_request", {"key": cache_key}) 
            return response_text
        except Exception as e:
            logger.error(f"❌ Groq Error: {e}", exc_info=True)
            return get_prompt(lang, "recipe_error")

    async def generate_recipe(self, dish_name: str, products: str, lang: str = "ru", user_id: int = 0, is_premium: bool = False) -> str:
        """Генерирует подробный рецепт. Добавляет КБЖУ для премиума."""
        system_prompt = get_prompt(lang, "recipe_generation")
        
        # !!! ВНЕДРЕНИЕ КБЖУ !!!
        if is_premium:
            nutrition_instr = get_prompt(lang, "nutrition_instruction")
            if nutrition_instr:
                system_prompt += f"\n\n{nutrition_instr}"
        
        user_prompt = get_prompt(lang, "recipe_generation_user").format(dish_name=dish_name, products=products)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            cache_type="recipe",
            lang=lang,
            user_id=user_id
        )
        return response

    # ... (analyze_products, generate_dishes_list, validate_recipe, determine_intent - БЕЗ ИЗМЕНЕНИЙ, ИХ КОД ЕСТЬ В ПРОШЛЫХ ОТВЕТАХ) ...
    # Я их опускаю для краткости, но они должны быть в файле!
    async def analyze_products(self, products: str, lang: str = "ru", user_id: int = 0) -> Optional[List[str]]:
        # ... (Код из предыдущих версий) ...
        # (Используйте финальную версию, где парсинг DICT/LIST)
        pass 
    async def generate_dishes_list(self, products: str, category: str, lang: str = "ru", user_id: int = 0) -> Optional[List[Dict]]:
         # ... (Код из предыдущих версий) ...
        pass
    async def validate_recipe(self, recipe_text: str, lang: str = "ru", user_id: int = 0) -> bool:
         # ... (Код из предыдущих версий) ...
        pass
    async def determine_intent(self, user_message: str, context: str, lang: str = "ru", user_id: int = 0) -> Dict:
         # ... (Код из предыдущих версий) ...
        pass

groq_service = GroqService()