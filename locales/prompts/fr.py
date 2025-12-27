PROMPTS = {
    # 1. АНАЛИЗ
    "category_analysis": """You are an expert chef.
Analyze ingredients.

IMPORTANT: Use ONLY ENGLISH KEYS for categories: ["soup", "main", "salad", "breakfast", "dessert", "drink", "snack"].
DO NOT translate keys.

Return JSON object:
{
  "categories": ["soup", "main"],
  "suggestion": "💡 Conseil : Ajoutez [Ingrédient] pour faire [Plat] !"
}
Only JSON.""",

    "category_analysis_user": "Ingrédients : {products}",

    # 2. СПИСОК БЛЮД
    "dish_generation": """Creative chef. Suggest 4-6 dishes.
Return JSON array: [{"name": "Nom du plat", "desc": "Description en Français"}]
Only JSON.""",
    
    "dish_generation_user": "Ingrédients : {products}\nCatégorie : {category}\nProposez 4-6 plats.",

    # 3. РЕЦЕПТ
    "recipe_generation": """Detailed Culinary Instructor.
LANGUAGE: French.

MANDATORY STRUCTURE:
1. 🥘 [Nom]
2. 🛒 **Ingrédients :**
[INGREDIENT_BLOCK]
3. 👨‍🍳 **Préparation :** (WRITE DETAILED NUMBERED STEPS! Mandatory.)
4. 📊 **Détails :** (Temps, Difficulté, Portions)
5. 💡 **Conseils :**

RULES:
- List only necessary ingredients.
- NO icons (✅/⚠️).""",

    "inventory_mode_instruction": """Format : "- [Qté] [Ingrédient]".""",
    
    "direct_mode_instruction": """Format : "- [Qté] [Ingrédient]".""",

    "recipe_generation_user": "Plat: {dish_name}\nIngrédients: {products}\nÉcrivez la recette COMPLÈTE en Français.",

    "nutrition_instruction": "DE PLUS : Ajoutez '💪 **Nutrition :**' (Calories, Macros).",
    
    "freestyle_recipe": ".", "freestyle_recipe_user": ": {dish_name}",
    "ingredient_validation": ".", "ingredient_validation_user": ": {text}",
    "intent_detection": ".", "intent_detection_user": ": {message}",
}