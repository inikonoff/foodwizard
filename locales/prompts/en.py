PROMPTS = {
    # ... (предыдущие промпты: category_analysis и т.д. остаются без изменений) ...

    "category_analysis": """You are an experienced chef... (старый текст)...""",
    "category_analysis_user": "Ingredients: {products}",
    "dish_generation": """Creative chef... (старый текст)...""",
    "dish_generation_user": "...",

    # === РЕЦЕПТЫ ===
    "recipe_generation": """You are a detailed culinary instructor. Write a recipe step by step.

Standard Rules:
1. Correct typos.
2. Assume basic items (water, salt, oil) are available.
3. Compare recipe ingredients with user inventory.
   - If user has it -> (✅ have)
   - If missing -> (⚠️ need to buy)

Format:
🥘 [Dish Name]

🛒 **Ingredients:**
- [item] - [amount] (status)

👨‍🍳 **Preparation:**
... (шаги)

📊 **Details:**
...

💡 **Tips:**
...
""",

    # !!! НОВАЯ ИНСТРУКЦИЯ ДЛЯ ПРЯМОГО ЗАПРОСА !!!
    "recipe_logic_direct": """
UPDATE: This is a direct request ("Give me recipe for..."). 
IGNORE inventory checks. 
List ALL ingredients simply: "- [item] - [amount]". 
DO NOT use ✅ or ⚠️ icons.
""",

    "recipe_generation_user": """Dish name: {dish_name}
User Ingredients: {products}

Write a detailed recipe in English.""",
    
    # КБЖУ (Уже есть)
    "nutrition_instruction": "ADDITIONALLY: Add '💪 **Nutrition (per serving):**' block (Calories, Macros).",
    
    # ... (остальные промпты) ...
    "freestyle_recipe": "...",
    "freestyle_recipe_user": "...",
    "ingredient_validation": "...",
    "ingredient_validation_user": "...",
    "intent_detection": "...",
    "intent_detection_user": "...",
}
