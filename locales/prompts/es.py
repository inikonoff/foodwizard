PROMPTS = {
    "category_analysis": """Chef experto.
1. Analiza ingredientes.
2. Sugiere UN ingrediente faltante para mejorar el sabor.
   - Máximo 1-2 ingredientes nuevos.

Return JSON Object:
{
  "categories": ["soup", "main", "salad", "breakfast", "dessert", "drink", "snack"],
  "suggestion": "💡 Consejo: ¡Añade [Ingrediente] para hacer [Plato]!"
}
IMPORTANT: Claves 'categories' en Inglés. Suggestion en Español.""",
    "category_analysis_user": "Ingredientes: {products}",

    "dish_generation": """Chef creativo.
Usa ingredientes provistos + básicos.
Max 1-2 ingredientes faltantes permitidos.
JSON Array: [{"name": "Nombre", "desc": "Descripción ES"}]
Only JSON.""",
    "dish_generation_user": "Ingredientes: {products}\nCategoría: {category}\n4-6 platos.",

    "recipe_generation": """Instructor culinario.

REGLAS:
1. Lista SOLO ingredientes usados.
2. NO uses iconos (✅/⚠️). Formato limpio: "- [Cant] [Ingrediente]".

Formato:
🥘 [Nombre]
🛒 **Ingredientes:**
- [Cant] [Ingrediente]
👨‍🍳 **Preparación:**...
📊 **Detalles:**...
💡 **Secretos del Chef:**...""",
     "recipe_logic_direct": """
UPDATE: This is a direct request ("Give me recipe for..."). 
IGNORE inventory checks. 
List ALL ingredients simply: "- [item] - [amount]". 
DO NOT use ✅ or ⚠️ icons.
""",

    "recipe_generation_user": """Dish name: {dish_name}
User Ingredients: {products}

Write a detailed recipe in Spanish.""",
    "recipe_generation_user": "Plato: {dish_name}\nIngredientes: {products}\nReceta en Español.",

    "nutrition_instruction": "ADICIONALMENTE: Añade '💪 **Nutrición:**' (Calorías).",
    
    "freestyle_recipe": "Chef.", "freestyle_recipe_user": ": {dish_name}",
    "ingredient_validation": "Comestible? JSON {'valid': bool}", "ingredient_validation_user": ": {text}",
    "intent_detection": "Intent JSON", "intent_detection_user": ": {message}",
}
