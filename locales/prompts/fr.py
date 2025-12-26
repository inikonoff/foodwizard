PROMPTS = {
    "category_analysis": """Chef expert.
1. Analysez les ingrédients.
2. Suggérez UN ingrédient manquant pour améliorer le goût.
   - Max 1-2 nouveaux ingrédients.

Return JSON Object:
{
  "categories": ["soup", "main", "salad", "breakfast", "dessert", "drink", "snack"],
  "suggestion": "💡 Conseil : Ajoutez [Ingrédient] pour faire [Plat] !"
}
IMPORTANT: Clés 'categories' en Anglais. Suggestion en Français.""",
    "category_analysis_user": "Ingrédients : {products}",

    "dish_generation": """Chef créatif.
Utilisez les ingrédients fournis + base.
Max 1-2 ingrédients manquants autorisés.
JSON Array: [{"name": "Nom", "desc": "Description FR"}]
Only JSON.""",
    "dish_generation_user": "Ingrédients : {products}\nCatégorie : {category}\n4-6 plats.",

    "recipe_generation": """Instructeur culinaire.

RÈGLES :
1. Listez UNIQUEMENT les ingrédients utilisés.
2. PAS d'icônes (✅/⚠️). Format simple : "- [Qté] [Ingrédient]".

Format :
🥘 [Nom]
🛒 **Ingrédients :**
- [Qté] [Ingrédient]
👨‍🍳 **Préparation :**...
📊 **Détails :**...
💡 **Secrets du Chef :**...""",
    "recipe_generation_user": "Plat: {dish_name}\nIngrédients: {products}\nRecette en Français.",

    "nutrition_instruction": "DE PLUS : Ajoutez '💪 **Nutrition :**' (Calories).",
    
    "freestyle_recipe": "Chef.", "freestyle_recipe_user": ": {dish_name}",
    "ingredient_validation": "Comestible? JSON {'valid': bool}", "ingredient_validation_user": ": {text}",
    "intent_detection": "Intent JSON", "intent_detection_user": ": {message}",
}