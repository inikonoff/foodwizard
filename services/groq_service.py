import logging
import json
import hashlib
from typing import Dict, List, Optional
from datetime import datetime

from groq import AsyncGroq
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_MAX_TOKENS
from database.cache import groq_cache
from database.metrics import metrics
from locales.prompts import get_prompt  # Импорт из locales/prompts/__init__.py

logger = logging.getLogger(__name__)

# Инициализация Groq клиента
client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

class GroqService:
    def __init__(self):
        if not client:
            logger.warning("Groq API ключ не установлен. Некоторые функции будут недоступны.")
    
    async def _send_request(self, system_prompt: str, user_prompt: str, 
                           temperature: float = 0.5, cache_type: str = "general", lang: str = "ru") -> str: # <-- lang ДОБАВЛЕН
        """Базовая функция отправки запроса с кэшированием"""
        if not client:
            return "Ошибка: API ключ не настроен."
        
        try:
            # Генерируем ключ кэша
            cache_key = groq_cache._generate_hash(f"{system_prompt[:100]}_{user_prompt[:200]}", lang, GROQ_MODEL)
            
            # Пытаемся получить из кэша
            cached_response = await groq_cache.get(
                prompt=cache_key,
                lang=lang,  # <-- ИСПОЛЬЗУЕМ ПРАВИЛЬНЫЙ ЯЗЫК ДЛЯ КЭША
                model=GROQ_MODEL,
                cache_type=cache_type
            )
            
            if cached_response:
                metrics.track_event(0, "groq_cache_hit", {"key": cache_key, "lang": lang})
                return cached_response

            # Отправка запроса Groq
            chat_completion = await client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=GROQ_MODEL,
                temperature=temperature,
                max_tokens=GROQ_MAX_TOKENS,
                response_format={"type": "json_object"} if cache_type in ["analysis", "validation", "intent"] else None
            )

            response_text = chat_completion.choices[0].message.content
            
            # Сохраняем в кэше
            await groq_cache.set(
                prompt=cache_key, # Используем хеш-ключ из _generate_hash
                response=response_text,
                lang=lang, # <-- ИСПОЛЬЗУЕМ ПРАВИЛЬНЫЙ ЯЗЫК
                model=GROQ_MODEL,
                tokens_used=chat_completion.usage.total_tokens,
                cache_type=cache_type
            )
            metrics.track_event(0, "groq_request", {"key": cache_key, "lang": lang})
            
            return response_text

        except Exception as e:
            logger.error(f"Ошибка Groq API: {e}")
            # Возвращаем универсальный промпт об ошибке
            return get_prompt(lang, "recipe_error")

    async def generate_recipe(self, dish_name: str, products: str, lang: str = "ru") -> str:
        """Генерирует подробный рецепт"""
        system_prompt = get_prompt(lang, "recipe_generation")
        user_prompt = get_prompt(lang, "recipe_generation_user").format(
            dish_name=dish_name,
            products=products
        )
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            cache_type="recipe",
            lang=lang # <-- ПЕРЕДАЕМ ЯЗЫК
        )
        
        return response

    async def analyze_products(self, products: str, lang: str = "ru") -> Optional[List[str]]:
        """Анализирует продукты и возвращает список категорий"""
        system_prompt = get_prompt(lang, "category_analysis")
        user_prompt = get_prompt(lang, "category_analysis_user").format(products=products)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            cache_type="analysis",
            lang=lang # <-- ПЕРЕДАЕМ ЯЗЫК
        )
        
        try:
            # Groq возвращает JSON массив строк
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            # Проверяем, что это список строк
            if isinstance(data, list) and all(isinstance(item, str) for item in data):
                return data
        except Exception as e:
            logger.error(f"Ошибка парсинга категорий: {e}")
        
        return None

    async def generate_dishes_list(self, products: str, category: str, lang: str = "ru") -> Optional[List[Dict]]:
        """Генерирует список из 5 блюд в выбранной категории"""
        system_prompt = get_prompt(lang, "dish_generation").format(category=category)
        user_prompt = get_prompt(lang, "dish_generation_user").format(products=products)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            cache_type="dish_list",
            lang=lang # <-- ПЕРЕДАЕМ ЯЗЫК
        )
        
        try:
            # Groq возвращает JSON массив объектов Dish
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            # Проверяем, что это список словарей
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                return data
        except Exception as e:
            logger.error(f"Ошибка парсинга списка блюд: {e}")
            
        return None

    async def validate_recipe(self, recipe_text: str, lang: str = "ru") -> bool:
        """Проверяет, содержит ли текст рецепта нежелательный контент"""
        system_prompt = get_prompt(lang, "recipe_validation")
        user_prompt = recipe_text
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            cache_type="validation",
            lang=lang # <-- ПЕРЕДАЕМ ЯЗЫК
        )
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            if isinstance(data, dict) and data.get("valid", False):
                return True
        except:
            pass
        
        return False
    
    async def determine_intent(self, user_message: str, context: str, lang: str = "ru") -> Dict:
        """Определяет намерение пользователя"""
        system_prompt = get_prompt(lang, "intent_detection")
        user_prompt = get_prompt(lang, "intent_detection_user").format(
            message=user_message,
            context=context
        )
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            cache_type="intent",
            lang=lang # <-- ПЕРЕДАЕМ ЯЗЫК
        )
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            if isinstance(data, dict):
                return data
        except Exception as e:
            logger.error(f"Ошибка парсинга интента: {e}")
        
        return {"intent": "products", "content": user_message} # Fallback

groq_service = GroqService()
        
