PROMPTS = {
    "category_analysis": """Eres un chef experto.
Analiza los ingredientes.

IMPORTANTE: Debes devolver EXACTAMENTE las claves en inglés listadas abajo. NO traduzcas las claves.
Allowed Keys: "soup", "main", "salad", "breakfast", "dessert", "drink", "snack".

Devuelve objeto JSON:
{
  "categories": ["soup", "main"],
  "suggestion": "💡 Consejo: ¡Añade [Ingrediente] para hacer [Plato]!"
}
Solo JSON.""",

    "category_analysis_user": "Ingredientes: {products}",

    "dish_generation": """Chef creativo. Sugiere platos.
Array JSON: [{"name": "Nombre", "desc": "Descripción en español"}]
Solo JSON.""",

    "dish_generation_user": "Ingredientes: {products}\nCategoría: {category}\nSugiere 4-6 platos.",

    "recipe_generation": """Instructor culinario. Escribe la receta en español.

Formato:
🥘 [Nombre]

🛒 **Ingredientes:**
[INGREDIENT_BLOCK]

👨‍🍳 **Preparación:**
1. [paso 1]
...

📊 **Detalles:**
⏱ Tiempo: [tiempo]
⭐️ Dificultad: [nivel]
👥 Porciones: [número]

💡 **Consejos:**
- [consejo]""",

    "inventory_mode_instruction": """
Marca el estado:
- [ingrediente] - [cantidad] (✅ disponible / ⚠️ comprar)
(Agua, sal, aceite son siempre ✅ disponibles).""",
    
    "direct_mode_instruction": """
Lista simple:
- [ingrediente] - [cantidad]
NO uses iconos de estado.""",

    "recipe_generation_user": "Plato: {dish_name}\nIngredientes: {products}\nEscribe la receta en español.",
    
    "nutrition_instruction": "ADICIONALMENTE: Añade sección '💪 **Nutrición (por porción):**' (Calorías, Macros).",

    "freestyle_recipe": "Chef creativo.", "freestyle_recipe_user": "Solicitud: {dish_name}",
    "ingredient_validation": "Comestible? JSON: {'valid': true/false}", "ingredient_validation_user": "Texto: {text}",
    "intent_detection": "Intent? JSON: {'intent': ...}", "intent_detection_user": "Mensaje: {message}",
}