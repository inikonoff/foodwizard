PROMPTS = {
    "category_analysis": """Chef esperto.
1. Analizza ingredienti.
2. Suggerisci UN ingrediente mancante.
   - Max 1-2 nuovi ingredienti.

Return JSON Object:
{
  "categories": ["soup", "main", "salad", "breakfast", "dessert", "drink", "snack"],
  "suggestion": "💡 Consiglio: Aggiungi [Ingrediente] per fare [Piatto]!"
}
IMPORTANT: Chiavi 'categories' in Inglese. Suggestion in Italiano.""",
    "category_analysis_user": "Ingredienti: {products}",

    "dish_generation": """Chef creativo.
Usa ingredienti forniti + base.
Max 1-2 ingredienti mancanti consentiti.
JSON Array: [{"name": "Nome", "desc": "Descrizione IT"}]
Only JSON.""",
    "dish_generation_user": "Ingredienti: {products}\nCategoria: {category}\n4-6 piatti.",

    "recipe_generation": """Istruttore culinario.

REGOLE:
1. Elenca SOLO ingredienti usati.
2. NO icone (✅/⚠️). Formato pulito: "- [Qtà] [Ingrediente]".

Formato:
🥘 [Nome]
🛒 **Ingredienti:**
- [Qtà] [Ingrediente]
👨‍🍳 **Preparazione:**...
📊 **Dettagli:**...
💡 **Segreti dello Chef:**...""",
     "recipe_logic_direct": """
UPDATE: This is a direct request ("Give me recipe for..."). 
IGNORE inventory checks. 
List ALL ingredients simply: "- [item] - [amount]". 
DO NOT use ✅ or ⚠️ icons.
""",

    "recipe_generation_user": """Dish name: {dish_name}
User Ingredients: {products}

Write a detailed recipe in English.""",
    "recipe_generation_user": "Piatto: {dish_name}\nIngredienti: {products}\nRicetta in Italiano.",

    "nutrition_instruction": "INOLTRE: Aggiungi '💪 **Nutrizione:**' (Calorie).",
    
    "freestyle_recipe": "Chef.", "freestyle_recipe_user": ": {dish_name}",
    "ingredient_validation": "?", "ingredient_validation_user": ": {text}",
    "intent_detection": "?", "intent_detection_user": ": {message}",
}
