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
        """Базовая функция отправки запроса"""
        if not self.client:
            return "Error: API key missing."
        
        try:
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
            # При ошибке возвращаем простой текст, не get_prompt, чтобы избежать рекурсии если и там ошибка
            return "Sorry, I couldn't generate the recipe at this moment."


    async def generate_recipe(self, dish_name: str, products: str, lang: str = "en", user_id: int = 0, is_premium: bool = False, is_direct: bool = False) -> str:
        """
        Генерирует рецепт.
        is_direct=True -> не проверяет наличие продуктов.
        is_premium=True -> добавляет КБЖУ.
        """
        # Базовый промпт
        system_prompt = get_prompt(lang, "recipe_generation")
        
        # 1. Логика для ПРЯМОГО ЗАПРОСА ("Дай рецепт...")
        if is_direct:
            direct_instruction = get_prompt(lang, "recipe_logic_direct")
            if direct_instruction:
                # Добавляем инструкцию, отменяющую проверки наличия
                system_prompt += f"\n\n{direct_instruction}"
        
        # 2. Логика для ПРЕМИУМА (КБЖУ)
        if is_premium:
            nutrition_instr = get_prompt(lang, "nutrition_instruction")
            if nutrition_instr:
                system_prompt += f"\n\n{nutrition_instr}"
        
        user_prompt = get_prompt(lang, "recipe_generation_user").format(
            dish_name=dish_name,
            products=products
        )
        
        # Чтобы кэш не смешивался для прямого/обычного запроса одного и того же блюда
        cache_marker = "DIRECT" if is_direct else "INVENTORY"
        user_prompt += f"\n[Context: {cache_marker}]"
        
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
        """Анализ продуктов"""
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
                    return {"categories": data, "suggestion": None}
            
            elif isinstance(data, dict):
                # Поддержка {categories: [], suggestion: ...}
                if "categories" in data and isinstance(data["categories"], list):
                    return data # Возвращаем весь словарь с советом
                # Поддержка старого формата {soup: true}
                return {"categories": [k for k, v in data.items() if v is True], "suggestion": None}

        except Exception as e:
            logger.error(f"Ошибка парсинга категорий: {e}", exc_info=True)
        
        return None

    async def generate_dishes_list(self, products: str, category: str, lang: str = "en", user_id: int = 0) -> Optional[List[Dict]]:
        """Генерация списка блюд"""
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

    # Заглушки (для полноты класса)
    async def validate_recipe(self, *args, **kwargs): return True
    async def determine_intent(self, *args, **kwargs): return {}

groq_service = GroqService()
