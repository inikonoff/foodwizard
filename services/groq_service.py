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
        if not GROQ_API_KEY:
            logger.warning("Groq API Key missing.")
            self.client = None
        else:
            self.client = AsyncGroq(api_key=GROQ_API_KEY)
            
    async def close(self):
        if self.client and hasattr(self.client, 'close'):
            await self.client.close()

    async def _send_request(self, system_prompt: str, user_prompt: str, 
                            temperature: float = 0.5, cache_type: str = "general", lang: str = "en", user_id: int = 0) -> str:
        if not self.client: return "API Error"
        
        try:
            cache_key = groq_cache._generate_hash(f"{system_prompt[:300]}_{user_prompt[:300]}", lang, GROQ_MODEL)
            cached = await groq_cache.get(prompt=cache_key, lang=lang, model=GROQ_MODEL, cache_type=cache_type)
            if cached:
                await metrics.track_event(user_id, "groq_cache_hit", {"key": cache_key})
                return cached

            is_json = cache_type in ["analysis", "validation", "intent", "dish_list"]
            if is_json and "json" not in system_prompt.lower():
                system_prompt += " Respond in JSON."

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
            logger.error(f"Groq API Error: {e}", exc_info=True)
            return "Server Error"

    # 1. АНАЛИЗ (ТУТ БЫЛИ ПРОБЛЕМЫ)
    async def analyze_products(self, products: str, lang: str = "en", user_id: int = 0) -> Optional[Dict]:
        system = get_prompt(lang, "category_analysis")
        user = get_prompt(lang, "category_analysis_user").format(products=products)
        
        # Temp 0.1 -> Максимальная строгость, минимум фантазий о рецептах
        response = await self._send_request(system, user, 0.1, "analysis", lang, user_id)
        
        logger.info(f"Analysis Raw: {response[:200]}...") 
        
        try:
            # Чистка
            if "{" not in response: raise ValueError("No JSON found")
            json_str = response[response.find('{'):response.rfind('}')+1]
            data = json.loads(json_str)
            
            result = {"categories": [], "suggestion": None}

            if isinstance(data, dict):
                # Проверяем все варианты, куда он мог запихнуть данные
                if "categories" in data:
                    result["categories"] = data["categories"]
                elif "category" in data:
                    result["categories"] = data["category"] # Некоторые модели путают s/без s
                
                # Фоллбэк: ищем любой список строк
                if not result["categories"]:
                    for v in data.values():
                        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], str):
                            result["categories"] = v
                            break

                result["suggestion"] = data.get("suggestion")
            
            if result["categories"]:
                return result
                
        except Exception as e:
            logger.error(f"Analysis Parse Error: {e}", exc_info=True)
        return None

    # 2. РЕЦЕПТ
    async def generate_recipe(self, dish_name: str, products: str, lang: str = "en", user_id: int = 0, is_premium: bool = False, is_direct: bool = False) -> str:
        base_prompt = get_prompt(lang, "recipe_generation")
        
        if is_direct:
            mode_instr = get_prompt(lang, "direct_mode_instruction")
            if not mode_instr: mode_instr = "List ingredients without checking availability."
        else:
            mode_instr = get_prompt(lang, "inventory_mode_instruction")
            if not mode_instr: mode_instr = "Check availability (✅/⚠️)."

        if "[INGREDIENT_BLOCK]" in base_prompt:
            system_prompt = base_prompt.replace("[INGREDIENT_BLOCK]", mode_instr)
        else:
            system_prompt = base_prompt + "\n" + mode_instr

        if is_premium:
            nutri = get_prompt(lang, "nutrition_instruction")
            if nutri: system_prompt += f"\n\n{nutri}"

        user_prompt = get_prompt(lang, "recipe_generation_user").format(dish_name=dish_name, products=products)
        marker = "DIRECT" if is_direct else "INVENTORY"
        user_prompt += f"\n[Mode: {marker}]"
        
        return await self._send_request(system_prompt, user_prompt, 0.7, "recipe", lang, user_id)

    # 3. СПИСОК БЛЮД
    async def generate_dishes_list(self, products: str, category: str, lang: str = "en", user_id: int = 0) -> Optional[List[Dict]]:
        sys = get_prompt(lang, "dish_generation")
        usr = get_prompt(lang, "dish_generation_user").format(products=products, category=category)
        resp = await self._send_request(sys, usr, 0.5, "dish_list", lang, user_id)
        try:
            if "{" not in resp and "[" not in resp: return None
            # Находим границы JSON
            start = resp.find('[')
            if start == -1: start = resp.find('{')
            end = resp.rfind(']')
            if end == -1: end = resp.rfind('}')
            
            clean = resp[start:end+1]
            data = json.loads(clean)
            
            if isinstance(data, list): return data
            if isinstance(data, dict):
                 if "dishes" in data: return data["dishes"]
                 for k, v in data.items(): 
                     if isinstance(v, list) and v and isinstance(v[0], dict): return v
        except: pass
        return None

    # Stubs
    async def validate_recipe(self, *a, **k): return True
    async def determine_intent(self, *a, **k): return {}

groq_service = GroqService()
