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
            return "Ошибка: API ключ не настроен."

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

            # Определяем, нужен ли JSON
            is_json = cache_type in ["analysis", "validation", "intent", "dish_list"]

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

            await metrics.track_event(user_id, "groq_request", {"key": cache_key, "lang": lang}) 

            return response_text

        except Exception as e:
            logger.error(f"Ошибка Groq API в _send_request: {e}", exc_info=True)
            return "" # Возвращаем пустую строку при ошибке

    async def analyze_products(self, products: str, lang: str = "ru", user_id: int = 0) -> Optional[List[str]]:
        """Анализирует продукты и возвращает список категорий"""
        
        # ЗАЩИТА: Не анализируем пустой текст или команды
        if not products or products.startswith('/') or len(products.strip()) < 2:
            return None

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

        if not response:
            return None

        logger.info(f"Сырой ответ Groq (анализ): {response[:200]}") 

        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)

            if isinstance(data, dict):
                 # Собираем только те ключи, где значение True
                 result = [key for key, value in data.items() if value is True]
                 return result if len(result) > 0 else None

            if isinstance(data, list) and all(isinstance(item, str) for item in data):
                return data if len(data) > 0 else None

        except Exception as e:
            logger.error(f"Ошибка парсинга категорий: {e}")

        return None

    # Остальные методы (generate_recipe, validate_recipe и т.д.) остаются без изменений
    # Но убедитесь, что везде добавлена проверка на пустой response

# Создаём глобальный экземпляр
groq_service = GroqService()