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
        """Sends request to Groq API with caching"""
        if not self.client:
            return "Error: API key missing."
        
        try:
            # Create a unique cache key based on prompt + context + language + model
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

            # Determine response format (JSON vs Text)
            is_json = cache_type in ["analysis", "validation", "intent", "dish_list"]
            
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
            logger.error(f"❌ Groq API Error in _send_request: {e}", exc_info=True)
            return get_prompt(lang, "recipe_error") or "Error generating response."


    async def generate_recipe(self, dish_name: str, products: str, lang: str = "en", user_id: int = 0, is_premium: bool = False, is_direct: bool = False) -> str:
        """
        Generates a detailed recipe.
        - Replaces [INGREDIENT_BLOCK] based on direct/inventory mode.
        - Appends Nutrition info if Premium.
        """
        # 1. Base Prompt
        system_prompt = get_prompt(lang, "recipe_generation")
        
        # 2. Determine Ingredient Mode Instruction
        if is_direct:
            # Clean list for direct request
            ingr_instruction = get_prompt(lang, "direct_mode_instruction")
            if not ingr_instruction: ingr_instruction = "List ingredients simply. No icons."
        else:
            # Check availability (Inventory mode)
            ingr_instruction = get_prompt(lang, "inventory_mode_instruction")
            if not ingr_instruction: ingr_instruction = "Check availability (✅/⚠️)."

        # 3. Inject Instruction into Placeholder
        if "[INGREDIENT_BLOCK]" in system_prompt:
            system_prompt = system_prompt.replace("[INGREDIENT_BLOCK]", ingr_instruction)
        else:
            system_prompt += f"\n\n{ingr_instruction}"

        # 4. Premium Nutrition Logic
        if is_premium:
            nutrition_instr = get_prompt(lang, "nutrition_instruction")
            if nutrition_instr:
                system_prompt += f"\n\n{nutrition_instr}"
        
        user_prompt = get_prompt(lang, "recipe_generation_user").format(
            dish_name=dish_name,
            products=products
        )
        
        # 5. Send Request
        return await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            cache_type="recipe",
            lang=lang,
            user_id=user_id
        )

    async def analyze_products(self, products: str, lang: str = "en", user_id: int = 0) -> Optional[Dict]:
        """
        Analyzes ingredients.
        Returns Dict: {"categories": ["main", "soup"], "suggestion": "Add X..."}
        """
        system_prompt = get_prompt(lang, "category_analysis")
        user_prompt = get_prompt(lang, "category_analysis_user").format(products=products)
        
        response = await self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3, # Lower temp for logical analysis
            cache_type="analysis",
            lang=lang,
            user_id=user_id
        )
        
        logger.info(f"Raw Analysis Response: {response[:200]}...") 
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            result = {"categories": [], "suggestion": None}
            
            if isinstance(data, list):
                # Legacy format support
                if all(isinstance(item, str) for item in data):
                    result["categories"] = data

            elif isinstance(data, dict):
                # Standard format
                # Extract Categories
                if "categories" in data and isinstance(data["categories"], list):
                     result["categories"] = data["categories"]
                else:
                     # Check keys {soup: true} style
                     result["categories"] = [k for k, v in data.items() if v is True and k != "suggestion"]

                # Extract Suggestion
                if "suggestion" in data:
                    result["suggestion"] = data["suggestion"]
            
            if result["categories"]:
                return result
                
        except Exception as e:
            logger.error(f"Analysis Parse Error: {e}", exc_info=True)
        
        return None

    async def generate_dishes_list(self, products: str, category: str, lang: str = "en", user_id: int = 0) -> Optional[List[Dict]]:
        """Generates list of dishes based on category"""
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
        
        logger.info(f"Raw Dish List Response: {response[:200]}...")
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            if isinstance(data, list):
                if all(isinstance(item, dict) for item in data):
                    return data
            
            elif isinstance(data, dict):
                # Search for list inside dict
                for key, value in data.items():
                    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                        return value
                        
        except Exception as e:
            logger.error(f"Dish List Parse Error: {e}", exc_info=True)
            
        return None

    # Stubs for unused but referenced methods
    async def validate_recipe(self, recipe_text, lang="en", user_id=0): return True
    async def determine_intent(self, user_message, context, lang="en", user_id=0): return {"intent": "products", "content": user_message}

groq_service = GroqService()