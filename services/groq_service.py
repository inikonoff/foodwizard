import logging
import json
import hashlib
from typing import Dict, List, Optional, Union
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
            logger.warning("Groq API Key missing.")
            self.client = None
        else:
            self.client = AsyncGroq(api_key=GROQ_API_KEY)
            
    async def close(self):
        if self.client and hasattr(self.client, 'close'):
            await self.client.close()
            logger.info("✅ Groq client session closed.")

    async def _send_request(self, system_prompt: str, user_prompt: str, 
                            temperature: float = 0.5, cache_type: str = "general", lang: str = "en", user_id: int = 0) -> str:
        """Базовая функция отправки запроса с кэшированием"""
        if not self.client:
            return "Error: API key missing."
        
        try:
            cache_key = groq_cache._generate_hash(f"{system_prompt[:300]}_{user_prompt[:300]}", lang, GROQ_MODEL)
            
            cached_response = await groq_cache.get(
                prompt=cache_key,
                lang=lang, 
                model=GROQ_MODEL,
                cache_type=cache_type
            )
            
            if cached_response:
                await metrics.track_event(user_id, "groq_cache_hit", {"key": cache_key, "lang": lang})
                return cached_response

            is_json = cache_type in ["analysis", "validation", "intent", "dish_list"]
            
            # !!! ФИКС ОШИБКИ 400 !!!
            # Groq требует явного слова "JSON" в system prompt при использовании json_object
            if is_json and "json" not in system_prompt.lower():
                system_prompt += " Respond in JSON."

            completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=GROQ_MODEL,
                temperature=temperature,
                max_tokens=GROQ_MAX_TOKENS,
                response_format={"type": "json_object"} if is_json else None,
                timeout=60.0
            )

            response_text = completion.choices[0].message.content
            
            await groq_cache.set(
                prompt=cache_key,
                response=response_text,
                lang=lang, 
                model=GROQ_MODEL,
                tokens_used=completion.usage.total_tokens,
                cache_type=cache_type
            )
            
            await metrics.track_event(user_id, "groq_request", {"key": cache_key, "lang": lang}) 
            return response_text

        except Exception as e:
            logger.error(f"❌ Ошибка Groq API в _send_request: {e}", exc_info=True)
            # Возвращаем текст ошибки, который точно НЕ является JSON, чтобы не ломать логику парсинга ниже
            return "Server Error"


    async def generate_recipe(self, dish_name: str, products: str, lang: str = "en", user_id: int = 0, is_premium: bool = False, is_direct: bool = False) -> str:
        system_prompt = get_prompt(lang, "recipe_generation")
        
        # 1. Логика для ПРЯМОГО ЗАПРОСА
        if is_direct:
            direct_instruction = get_prompt(lang, "direct_mode_instruction")
            if not direct_instruction: direct_instruction = "List ingredients simply."
            
            if "[INGREDIENT_BLOCK]" in system_prompt:
                system_prompt = system_prompt.replace("[INGREDIENT_BLOCK]", direct_instruction)
            else:
                system_prompt += f"\n\n{direct_instruction}"
        else:
            # Логика для ИНВЕНТАРЯ (Галочки)
            inventory_instruction = get_prompt(lang, "inventory_mode_instruction")
            if not inventory_instruction: inventory_instruction = "Mark items with ✅/⚠️."
            
            if "[INGREDIENT_BLOCK]" in system_prompt:
                system_prompt = system_prompt.replace("[INGREDIENT_BLOCK]", inventory_instruction)
            else:
                system_prompt += f"\n\n{inventory_instruction}"

        # 2. Логика для ПРЕМИУМА (КБЖУ)
        if is_premium:
            nutrition_instr = get_prompt(lang, "nutrition_instruction")
            if nutrition_instr:
                system_prompt += f"\n\n{nutrition_instr}"
        
        user_prompt = get_prompt(lang, "recipe_generation_user").format(
            dish_name=dish_name,
            products=products
        )
        
        cache_marker = "DIRECT" if is_direct else "INVENTORY"
        user_prompt += f"\n[Context: {cache_marker}]"
        
        return await self._send_request(system_prompt, user_prompt, 0.7, "recipe", lang, user_id)

    async def analyze_products(self, products: str, lang: str = "en", user_id: int = 0) -> Optional[Dict]:
        system_prompt = get_prompt(lang, "category_analysis")
        user_prompt = get_prompt(lang, "category_analysis_user").format(products=products)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1, # Низкая температура для строгой логики
            cache_type="analysis",
            lang=lang,
            user_id=user_id
        )
        
        logger.info(f"Сырой ответ Groq (анализ): {response[:200]}...") 
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            result = {"categories": [], "suggestion": None}
            
            if isinstance(data, list):
                if all(isinstance(item, str) for item in data):
                    result["categories"] = data

            elif isinstance(data, dict):
                if "categories" in data and isinstance(data["categories"], list):
                    result["categories"] = data["categories"]
                else:
                    # Старый формат {soup: true}
                    result["categories"] = [k for k, v in data.items() if v is True and k != "suggestion"]

                if "suggestion" in data:
                    result["suggestion"] = data["suggestion"]
            
            if result["categories"]:
                return result
                
        except Exception as e:
            logger.error(f"Ошибка парсинга категорий: {e}", exc_info=True)
        
        return None

    async def generate_dishes_list(self, products: str, category: str, lang: str = "en", user_id: int = 0) -> Optional[List[Dict]]:
        system_prompt = get_prompt(lang, "dish_generation")
        user_prompt = get_prompt(lang, "dish_generation_user").format(products=products, category=category)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            cache_type="dish_list",
            lang=lang,
            user_id=user_id
        )
        
        logger.info(f"Сырой ответ Groq (блюда): {response[:200]}...")
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            if isinstance(data, list):
                if all(isinstance(item, dict) for item in data):
                    return data
            
            elif isinstance(data, dict):
                # Ищем список внутри
                for key, value in data.items():
                    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                        return value
                        
        except Exception as e:
            logger.error(f"Ошибка парсинга списка блюд: {e}", exc_info=True)
            
        return None

    async def validate_recipe(self, recipe_text: str, lang: str = "en", user_id: int = 0) -> bool:
        return True # Заглушка, можно расширить позже
    
    async def determine_intent(self, user_message: str, context: str, lang: str = "en", user_id: int = 0) -> Dict:
        return {"intent": "products", "content": user_message} # Заглушка

groq_service = GroqService()
