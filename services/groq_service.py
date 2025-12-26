import logging
import json
import hashlib
from typing import Dict, List, Optional
from groq import AsyncGroq 
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_MAX_TOKENS
from database.cache import groq_cache
from database.metrics import metrics
from locales.prompts import get_prompt 

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        self.client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
            
    async def close(self):
        if self.client: await self.client.close()

    async def _send_request(self, system_prompt: str, user_prompt: str, 
                            temperature: float = 0.5, cache_type: str = "general", lang: str = "en", user_id: int = 0) -> str:
        if not self.client: return "API Key Error"
        
        try:
            cache_key = groq_cache._generate_hash(f"{system_prompt[:300]}_{user_prompt[:300]}", lang, GROQ_MODEL)
            cached = await groq_cache.get(prompt=cache_key, lang=lang, model=GROQ_MODEL, cache_type=cache_type)
            if cached:
                await metrics.track_event(user_id, "groq_cache_hit", {"key": cache_key})
                return cached

            is_json = cache_type in ["analysis", "validation", "intent", "dish_list"]
            
            completion = await self.client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                model=GROQ_MODEL, temperature=temperature, max_tokens=GROQ_MAX_TOKENS,
                response_format={"type": "json_object"} if is_json else None,
                timeout=60.0
            )
            text = completion.choices[0].message.content
            await groq_cache.set(prompt=cache_key, response=text, lang=lang, model=GROQ_MODEL, tokens_used=completion.usage.total_tokens, cache_type=cache_type)
            await metrics.track_event(user_id, "groq_request", {"key": cache_key}) 
            return text
        except Exception as e:
            logger.error(f"Groq Error: {e}", exc_info=True)
            return get_prompt(lang, "recipe_error")

    # --- MAIN LOGIC UPDATED ---
    async def generate_recipe(self, dish_name: str, products: str, lang: str = "en", user_id: int = 0, is_premium: bool = False, is_direct: bool = False) -> str:
        # 1. Получаем базу шаблона
        system_prompt = get_prompt(lang, "recipe_generation")
        
        # 2. Выбираем режим ингредиентов
        if is_direct:
            # Чистый список для "Дай рецепт пиццы"
            ingr_mode = get_prompt(lang, "direct_mode_instruction")
            if not ingr_mode: ingr_mode = "List ingredients simply. No icons."
        else:
            # Список с проверкой наличия
            ingr_mode = get_prompt(lang, "inventory_mode_instruction")
            if not ingr_mode: ingr_mode = "Check availability (✅/⚠️)."

        # 3. Внедряем режим в шаблон (заменяем плейсхолдер)
        if "[INGREDIENT_BLOCK]" in system_prompt:
            system_prompt = system_prompt.replace("[INGREDIENT_BLOCK]", ingr_mode)
        else:
            # Fallback для старых файлов промптов
            system_prompt += f"\n\n{ingr_mode}"
            
        # 4. Внедряем КБЖУ для Премиума
        if is_premium:
            nutri = get_prompt(lang, "nutrition_instruction")
            if nutri: system_prompt += f"\n\n{nutri}"

        user_prompt = get_prompt(lang, "recipe_generation_user").format(dish_name=dish_name, products=products)
        
        return await self._send_request(system_prompt, user_prompt, 0.7, "recipe", lang, user_id)

    # --- REST ---
    async def analyze_products(self, products: str, lang: str = "en", user_id: int = 0) -> Optional[Dict]:
        sys = get_prompt(lang, "category_analysis")
        usr = get_prompt(lang, "category_analysis_user").format(products=products)
        resp = await self._send_request(sys, usr, 0.3, "analysis", lang, user_id)
        try:
            data = json.loads(resp.replace("```json","").replace("```","").strip())
            # Нормализация
            res = {"categories": [], "suggestion": None}
            if isinstance(data, list): res["categories"] = data
            elif isinstance(data, dict):
                 res["categories"] = data.get("categories", [])
                 if not res["categories"]: # old format fallback
                     res["categories"] = [k for k,v in data.items() if v is True and k!="suggestion"]
                 res["suggestion"] = data.get("suggestion")
            if res["categories"]: return res
        except: pass
        return None

    async def generate_dishes_list(self, products: str, category: str, lang: str = "en", user_id: int = 0) -> Optional[List[Dict]]:
        sys = get_prompt(lang, "dish_generation")
        usr = get_prompt(lang, "dish_generation_user").format(products=products, category=category)
        resp = await self._send_request(sys, usr, 0.5, "dish_list", lang, user_id)
        try:
            d = json.loads(resp.replace("```json","").replace("```","").strip())
            if isinstance(d, list): return d
            if isinstance(d, dict): # Search inside dict
                 for k, v in d.items(): 
                     if isinstance(v, list) and v and isinstance(v[0], dict): return v
        except: pass
        return None

    async def validate_recipe(self, *a, **k): return True
    async def determine_intent(self, *a, **k): return {}

groq_service = GroqService()