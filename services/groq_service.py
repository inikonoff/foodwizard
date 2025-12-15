import logging
import json
import hashlib
from typing import Dict, List, Optional
from datetime import datetime

from groq import AsyncGroq
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_MAX_TOKENS
from database.cache import groq_cache
from database.metrics import metrics
from locales.prompts import get_prompt

logger = logging.getLogger(__name__)

# Инициализация Groq клиента
client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

class GroqService:
    def __init__(self):
        if not client:
            logger.warning("Groq API ключ не установлен. Некоторые функции будут недоступны.")
    
    async def _send_request(self, system_prompt: str, user_prompt: str, 
                           temperature: float = 0.5, cache_type: str = "general") -> str:
        """Базовая функция отправки запроса с кэшированием"""
        if not client:
            return "Ошибка: API ключ не настроен."
        
        try:
            # Генерируем ключ кэша
            cache_key = f"{system_prompt[:100]}_{user_prompt[:200]}_{temperature}"
            
            # Пытаемся получить из кэша
            cached_response = await groq_cache.get(
                prompt=cache_key,
                lang="en",  # Промпты на английском для кэша
                model=GROQ_MODEL,
                cache_type=cache_type
            )
            
            if cached_response:
                logger.info(f"Использую кэшированный ответ для {cache_type}")
                return cached_response
            
            # Если нет в кэше, делаем запрос к Groq
            response = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=GROQ_MAX_TOKENS,
                temperature=temperature
            )
            
            result = response.choices[0].message.content.strip()
            
            # Сохраняем в кэш
            await groq_cache.set(
                prompt=cache_key,
                lang="en",
                model=GROQ_MODEL,
                response=result,
                cache_type=cache_type,
                tokens_used=response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else None
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка Groq API: {e}")
            return ""
    
    async def analyze_products(self, products: str, lang: str = "ru") -> List[str]:
        """Анализирует продукты и возвращает доступные категории"""
        system_prompt = get_prompt(lang, "category_analysis")
        user_prompt = get_prompt(lang, "category_analysis_user").format(products=products)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            cache_type="analysis"
        )
        
        try:
            # Очищаем JSON от возможных markdown
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            if isinstance(data, list):
                return data
        except Exception as e:
            logger.error(f"Ошибка парсинга категорий: {e}")
        
        # Fallback категории
        return ["main", "salad"]
    
    async def generate_dish_list(self, products: str, category: str, lang: str = "ru") -> List[Dict[str, str]]:
        """Генерирует список блюд для выбранной категории"""
        system_prompt = get_prompt(lang, "dish_generation")
        user_prompt = get_prompt(lang, "dish_generation_user").format(
            products=products,
            category=category
        )
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6,
            cache_type="dish_list"
        )
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            if isinstance(data, list):
                return data
        except Exception as e:
            logger.error(f"Ошибка парсинга списка блюд: {e}")
        
        return []
    
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
            temperature=0.4,
            cache_type="recipe"
        )
        
        # Добавляем стандартное завершение
        if response:
            footer = get_prompt(lang, "recipe_footer")
            return f"{response}\n\n{footer}"
        
        return get_prompt(lang, "recipe_error")
    
    async def generate_freestyle_recipe(self, dish_name: str, lang: str = "ru") -> str:
        """Генерирует рецепт по названию блюда без учёта продуктов"""
        system_prompt = get_prompt(lang, "freestyle_recipe")
        user_prompt = get_prompt(lang, "freestyle_recipe_user").format(dish_name=dish_name)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            cache_type="freestyle_recipe"
        )
        
        if response:
            footer = get_prompt(lang, "recipe_footer")
            return f"{response}\n\n{footer}"
        
        return get_prompt(lang, "recipe_error")
    
    async def validate_ingredients(self, text: str, lang: str = "ru") -> bool:
        """Проверяет, является ли текст списком продуктов"""
        system_prompt = get_prompt(lang, "ingredient_validation")
        user_prompt = get_prompt(lang, "ingredient_validation_user").format(text=text)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            cache_type="validation"
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
            cache_type="intent"
        )
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            if isinstance(data, dict):
                return data
        except Exception as e:
            logger.error(f"Ошибка парсинга интента: {e}")
        
        return {"intent": "unclear", "products": "", "dish_name": ""}

# Создаём глобальный экземпляр
groq_service = GroqService()
