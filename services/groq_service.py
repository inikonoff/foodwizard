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
            logger.warning("Groq API ключ не установлен. Некоторые функции будут недоступны.")
            self.client = None
        else:
            self.client = AsyncGroq(api_key=GROQ_API_KEY)

    async def close(self):
        """Закрывает HTTP-сессию клиента Groq"""
        if self.client and hasattr(self.client, 'close'):
            await self.client.close()
            logger.info("✅ Groq client session closed.")

    async def _send_request(self, system_prompt: str, user_prompt: str, 
                            temperature: float = 0.5, cache_type: str = "general", lang: str = "ru", user_id: int = 0) -> str:
        """Базовая функция отправки запроса с кэшированием"""
        if not self.client:
            return ""

        try:
            # Генерируем ключ кэша
            cache_key = groq_cache._generate_hash(f"{system_prompt[:100]}_{user_prompt[:200]}", lang, GROQ_MODEL)

            # Пытаемся получить из кэша
            cached_response = await groq_cache.get(
                prompt=cache_key,
                lang=lang, 
                model=GROQ_MODEL,
                cache_type=cache_type
            )

            if cached_response:
                await metrics.track_event(user_id, "groq_cache_hit", {"key": cache_key, "lang": lang})
                return cached_response

            # Определяем формат ответа (JSON для структурированных данных)
            is_json = cache_type in ["analysis", "dish_list"]

            # Отправка запроса Groq
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=GROQ_MODEL,
                temperature=temperature,
                max_tokens=GROQ_MAX_TOKENS,
                response_format={"type": "json_object"} if is_json else None
            )

            response_text = chat_completion.choices[0].message.content

            # Сохраняем в кэше
            await groq_cache.set(
                prompt=cache_key,
                response=response_text,
                lang=lang, 
                model=GROQ_MODEL,
                tokens_used=chat_completion.usage.total_tokens,
                cache_type=cache_type
            )

            await metrics.track_event(user_id, "groq_request", {"key": cache_key, "lang": lang, "type": cache_type}) 

            return response_text

        except Exception as e:
            logger.error(f"❌ Ошибка Groq API в _send_request: {e}", exc_info=True)
            return ""

    async def analyze_products(self, products: str, lang: str = "ru", user_id: int = 0) -> Optional[List[str]]:
        """Анализирует продукты и возвращает список категорий"""
        if not products or len(products.strip()) < 2:
            return None

        system_prompt = get_prompt(lang, "category_analysis")
        user_prompt = get_prompt(lang, "category_analysis_user").format(products=products)

        response = await self._send_request(system_prompt, user_prompt, 0.1, "analysis", lang, user_id)

        if not response:
            return None

        try:
            data = json.loads(response)
            if isinstance(data, dict):
                return [key for key, value in data.items() if value is True]
            if isinstance(data, list):
                return data
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга категорий: {e}")
        return None

    async def generate_dishes_from_products(self, products: str, category: str, lang: str = "ru", user_id: int = 0) -> List[dict]:
        """Генерирует список названий блюд (то, что вызывается в recipes.py)"""
        system_prompt = get_prompt(lang, "dish_list_generation")
        user_prompt = get_prompt(lang, "dish_list_user").format(products=products, category=category)

        response = await self._send_request(system_prompt, user_prompt, 0.7, "dish_list", lang, user_id)

        if not response:
            return []

        try:
            data = json.loads(response)
            # Обработка разных форматов ответа нейросети
            if isinstance(data, dict) and "dishes" in data:
                return data["dishes"]
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга списка блюд: {e}")
            return []

    async def generate_recipe(self, dish_name: str, products: str, lang: str = "ru", user_id: int = 0) -> str:
        """Генерирует финальный текст рецепта"""
        system_prompt = get_prompt(lang, "recipe_generation")
        user_prompt = get_prompt(lang, "recipe_user").format(dish_name=dish_name, products=products)

        response = await self._send_request(system_prompt, user_prompt, 0.7, "recipe", lang, user_id)
        
        return response if response else "Извините, возникла ошибка при создании рецепта."

# Создаём глобальный экземпляр для импорта в хендлерах
groq_service = GroqService()