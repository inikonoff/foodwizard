PROMPTS = {
    # 1. АНАЛИЗ (STRICT KEYS FROM EN)
    "category_analysis": """You are an expert chef.
Analyze ingredients.

IMPORTANT: Use ONLY ENGLISH KEYS for categories: ["soup", "main", "salad", "breakfast", "dessert", "drink", "snack"].
DO NOT translate keys into Italian (e.g. do NOT use 'zuppe').

Return JSON object:
{
  "categories": ["soup", "main"],
  "suggestion": "💡 Consiglio: Aggiungi [Ingrediente] per fare [Piatto]!"
}
Only JSON.""",

    "category_analysis_user": "Ingredienti: {products}",

    # 2. СПИСОК БЛЮД
    "dish_generation": """Creative chef. Suggest 4-6 dishes.
Return JSON array of objects: [{"name": "Nome Piatto", "desc": "Descrizione in Italiano"}]
Only JSON.""",
    
    "dish_generation_user": "Ingredienti: {products}\nCategoria: {category}\nSuggerisci 4-6 piatti.",

    # 3. РЕЦЕПТ (ЭТАЛОН)
    "recipe_generation": """Detailed Culinary Instructor.
LANGUAGE: Italian.

MANDATORY STRUCTURE:
1. 🥘 [Nome Piatto]
2. 🛒 **Ingredienti:**
[INGREDIENT_BLOCK]
3. 👨‍🍳 **Preparazione:** (WRITE DETAILED NUMBERED STEPS! Do not skip.)
4. 📊 **Dettagli:** (Tempo, Livello, Porzioni)
5. 💡 **Consigli:**

INGREDIENT RULES:
- Filter out unused user inputs.
- Do NOT use status icons like ✅/⚠️ in the final list. Just amount + name.""",

    "inventory_mode_instruction": """Format: "- [Qtà] [Ingrediente]".""",
    
    "direct_mode_instruction": """Format: "- [Qtà] [Ingrediente]".""",

    "recipe_generation_user": "Piatto: {dish_name}\nIngredienti: {products}\nScrivi la ricetta COMPLETA in Italiano.",

    "nutrition_instruction": "INOLTRE: Aggiungi '💪 **Valori nutrizionali:**' (Calorie, Macro).",
    
    "freestyle_recipe": ".", "freestyle_recipe_user": ": {dish_name}",
    "ingredient_validation": ".", "ingredient_validation_user": ": {text}",
    "intent_detection": ".", "intent_detection_user": ": {message}",
}