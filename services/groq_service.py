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
    # Алиас для обратной совместимости (временно)
    async def generate_dishes_list(self, products: str, category: str, lang: str = "ru") -> List[Dict[str, str]]:
        """Алиас для generate_dish_list (для обратной совместимости)"""
        logger.warning("⚠️ Используется устаревший метод generate_dishes_list. Используйте generate_dish_list")
        return await self.generate_dish_list(products, category, lang)
    
    async def _send_request(self, system_prompt: str, user_prompt: str, 
                           temperature: float = 0.5, cache_type: str = "general") -> str:
        """Базовая функция отправки запроса с кэшированием"""
        if not client:
            logger.error("Groq клиент не инициализирован")
            return ""
        
        try:
            # Генерируем ключ кэша
            cache_key = f"{system_prompt[:100]}_{user_prompt[:200]}_{temperature}"
            
            # Пытаемся получить из кэша
            cached_response = await groq_cache.get(
                prompt=cache_key,
                lang="en",
                model=GROQ_MODEL,
                cache_type=cache_type
            )
            
            if cached_response:
                logger.info(f"✅ Использую кэшированный ответ для {cache_type}")
                return cached_response
            
            logger.info(f"🔄 Отправка запроса к Groq API (тип: {cache_type})")
            
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
            
            logger.info(f"✅ Получен ответ от Groq API (длина: {len(result)})")
            
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
            logger.error(f"❌ Ошибка Groq API: {e}", exc_info=True)
            return ""
    
    async def analyze_products(self, products: str, lang: str = "ru") -> List[str]:
        """Анализирует продукты и возвращает доступные категории"""
        logger.info(f"📊 Анализ продуктов: {products[:50]}...")
        
        system_prompt = get_prompt(lang, "category_analysis")
        user_prompt = get_prompt(lang, "category_analysis_user").format(products=products)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            cache_type="analysis"
        )
        
        if not response:
            logger.error("❌ Пустой ответ от Groq при анализе категорий")
            return ["main", "salad"]  # Fallback
        
        try:
            # Очищаем JSON от возможных markdown
            clean_json = response.replace("```json", "").replace("```", "").strip()
            logger.info(f"📝 Ответ Groq (категории): {clean_json}")
            
            data = json.loads(clean_json)
            
            if isinstance(data, list) and len(data) > 0:
                logger.info(f"✅ Найдено категорий: {len(data)}")
                return data
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга категорий: {e}")
            logger.error(f"Ответ был: {response}")
        
        # Fallback категории
        logger.warning("⚠️ Используем fallback категории")
        return ["main", "salad"]
    
    async def generate_dish_list(self, products: str, category: str, lang: str = "ru") -> List[Dict[str, str]]:
        """Генерирует список блюд для выбранной категории"""
        logger.info(f"🍳 Генерация списка блюд для категории: {category}")
        
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
        
        if not response:
            logger.error("❌ Пустой ответ от Groq при генерации блюд")
            return []
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            logger.info(f"📝 Ответ Groq (блюда): {clean_json[:200]}...")
            
            data = json.loads(clean_json)
            
            if isinstance(data, list) and len(data) > 0:
                logger.info(f"✅ Сгенерировано блюд: {len(data)}")
                return data
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга списка блюд: {e}")
            logger.error(f"Ответ был: {response}")
        
        return []
    
    async def generate_recipe(self, dish_name: str, products: str, lang: str = "ru") -> str:
        """Генерирует подробный рецепт"""
        logger.info(f"📖 Генерация рецепта для: {dish_name}")
        
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
        
        if not response:
            logger.error("❌ Пустой ответ от Groq при генерации рецепта")
            return get_prompt(lang, "recipe_error")
        
        # Добавляем стандартное завершение
        footer = get_prompt(lang, "recipe_footer")
        logger.info(f"✅ Рецепт сгенерирован (длина: {len(response)})")
        return f"{response}\n\n{footer}"
    
    async def generate_freestyle_recipe(self, dish_name: str, lang: str = "ru") -> str:
        """Генерирует рецепт по названию блюда без учёта продуктов"""
        logger.info(f"🎨 Генерация freestyle рецепта для: {dish_name}")
        
        system_prompt = get_prompt(lang, "freestyle_recipe")
        user_prompt = get_prompt(lang, "freestyle_recipe_user").format(dish_name=dish_name)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            cache_type="freestyle_recipe"
        )
        
        if not response:
            logger.error("❌ Пустой ответ от Groq при генерации freestyle рецепта")
            return get_prompt(lang, "recipe_error")
        
        footer = get_prompt(lang, "recipe_footer")
        logger.info(f"✅ Freestyle рецепт сгенерирован (длина: {len(response)})")
        return f"{response}\n\n{footer}"
    
    async def validate_ingredients(self, text: str, lang: str = "ru") -> bool:
        """Проверяет, является ли текст списком продуктов"""
        logger.info(f"🔍 Валидация ингредиентов: {text[:50]}...")
        
        system_prompt = get_prompt(lang, "ingredient_validation")
        user_prompt = get_prompt(lang, "ingredient_validation_user").format(text=text)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            cache_type="validation"
        )
        
        if not response:
            logger.error("❌ Пустой ответ от Groq при валидации")
            return False
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            logger.info(f"📝 Ответ Groq (валидация): {clean_json}")
            
            data = json.loads(clean_json)
            
            if isinstance(data, dict):
                is_valid = data.get("valid", False)
                logger.info(f"✅ Валидация: {is_valid}")
                return is_valid
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга валидации: {e}")
        
        return False
    
    async def determine_intent(self, user_message: str, context: str, lang: str = "ru") -> Dict:
        """Определяет намерение пользователя"""
        logger.info(f"🤔 Определение интента для: {user_message[:50]}...")
        
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
        
        if not response:
            logger.error("❌ Пустой ответ от Groq при определении интента")
            return {"intent": "unclear", "products": "", "dish_name": ""}
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            logger.info(f"📝 Ответ Groq (интент): {clean_json}")
            
            data = json.loads(clean_json)
            
            if isinstance(data, dict):
                logger.info(f"✅ Интент определён: {data.get('intent')}")
                return data
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга интента: {e}")
        
        return {"intent": "unclear", "products": "", "dish_name": ""}

# Создаём глобальный экземпляр
groq_service = GroqService()

