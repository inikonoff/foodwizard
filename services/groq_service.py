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
            logger.info("✅ Groq client session closed.")

    async def _send_request(self, system_prompt: str, user_prompt: str, 
                            temperature: float = 0.5, cache_type: str = "general", lang: str = "en", user_id: int = 0) -> str:
        """Базовая функция отправки запроса с кэшированием"""
        if not self.client:
            return "Error: API key missing."
        
        try:
            # Генерируем ключ кэша
            cache_key = groq_cache._generate_hash(f"{system_prompt[:200]}_{user_prompt[:200]}", lang, GROQ_MODEL)
            
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
            
            chat_completion = await self.client.chat.completions.create(
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

            response_text = chat_completion.choices[0].message.content
            
            await groq_cache.set(
                prompt=cache_key,
                response=response_text,
                lang=lang, 
                model=GROQ_MODEL,
                tokens_used=chat_completion.usage.total_tokens,
                cache_type=cache_type
            )
            
            await metrics.track_event(user_id, "groq_request", {"key": cache_key, "lang": lang}) 
            return response_text

        except Exception as e:
            logger.error(f"❌ Ошибка Groq API в _send_request: {e}", exc_info=True)
            return get_prompt(lang, "recipe_error")


    async def generate_recipe(self, dish_name: str, products: str, lang: str = "en", user_id: int = 0, is_premium: bool = False) -> str:
        """Генерирует подробный рецепт. Добавляет КБЖУ для премиума."""
        system_prompt = get_prompt(lang, "recipe_generation")
        
        # Внедрение КБЖУ
        if is_premium:
            nutrition_instr = get_prompt(lang, "nutrition_instruction")
            if nutrition_instr:
                system_prompt += f"\n\n{nutrition_instr}"
        
        user_prompt = get_prompt(lang, "recipe_generation_user").format(
            dish_name=dish_name,
            products=products
        )
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            cache_type="recipe",
            lang=lang,
            user_id=user_id
        )
        
        return response

    async def analyze_products(self, products: str, lang: str = "en", user_id: int = 0) -> Optional[List[str]]:
        """Анализирует продукты и возвращает список категорий"""
        system_prompt = get_prompt(lang, "category_analysis")
        user_prompt = get_prompt(lang, "category_analysis_user").format(products=products)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            cache_type="analysis",
            lang=lang,
            user_id=user_id
        )
        
        logger.info(f"Сырой ответ Groq (анализ): {response[:200]}...") 
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            if isinstance(data, list):
                if all(isinstance(item, str) for item in data):
                    return data
            
            elif isinstance(data, dict):
                # Поддержка формата {"categories": [...]}
                if "categories" in data and isinstance(data["categories"], list):
                    return data["categories"]
                # Поддержка формата {"soup": true}
                return [key for key, value in data.items() if value is True]

        except Exception as e:
            logger.error(f"Ошибка парсинга категорий: {e}", exc_info=True)
        
        return None

    async def generate_dishes_list(self, products: str, category: str, lang: str = "en", user_id: int = 0) -> Optional[List[Dict]]:
        """Генерирует список из 5 блюд в выбранной категории"""
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
                # Ищем список внутри словаря
                for key, value in data.items():
                    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                        return value
                        
        except Exception as e:
            logger.error(f"Ошибка парсинга списка блюд: {e}", exc_info=True)
            
        return None

    async def validate_recipe(self, recipe_text: str, lang: str = "en", user_id: int = 0) -> bool:
        """Проверяет контент"""
        system_prompt = get_prompt(lang, "recipe_validation")
        user_prompt = recipe_text
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            cache_type="validation",
            lang=lang,
            user_id=user_id
        )
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            if isinstance(data, dict) and data.get("valid", False):
                return True
        except Exception as e:
            logger.error(f"Ошибка парсинга валидации: {e}", exc_info=True)
        
        return False
    
    async def determine_intent(self, user_message: str, context: str, lang: str = "en", user_id: int = 0) -> Dict:
        """Определяет намерение"""
        system_prompt = get_prompt(lang, "intent_detection")
        user_prompt = get_prompt(lang, "intent_detection_user").format(message=user_message, context=context)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            cache_type="intent",
            lang=lang,
            user_id=user_id
        )
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            if isinstance(data, dict):
                return data
        except Exception as e:
            logger.error(f"Ошибка парсинга интента: {e}", exc_info=True)
        
        return {"intent": "products", "content": user_message}

groq_service = GroqService()