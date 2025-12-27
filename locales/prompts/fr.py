PROMPTS = {
    "category_analysis": """Vous êtes un Chef IA.
1. Analysez les ingrédients.
2. Choisissez des catégories PERTINENTES (pas de dessert si seulement viande).

IMPORTANT : Les clés JSON doivent rester en ANGLAIS : ["soup", "main", "salad", "breakfast", "dessert", "drink", "snack"].
NE PAS TRADUIRE LES CLÉS DANS LE JSON.

Output JSON:
{
  "categories": ["main", "soup"],
  "suggestion": "💡 Conseil : Ajoutez [Ingrédient] !"
}""",

    "category_analysis_user": "Ingrédients: {products}",

    "dish_generation": """Chef créatif. Suggérez 4-6 plats.
JSON Array: [{"name": "Nom", "desc": "Description en Français"}]
Uniquement JSON.""",
    "dish_generation_user": "Ingrédients : {products}\nCatégorie : {category}\n4-6 plats.",

    "recipe_generation": """Instructeur culinaire.
LANGUE : Français.

STRUCTURE OBLIGATOIRE :
1. 🥘 Titre
2. 🛒 Ingrédients
3. 👨‍🍳 Préparation (Étapes détaillées. INDISPENSABLE !)
4. 📊 Détails
5. 💡 Conseils

RÈGLES INGRÉDIENTS :
- [INGREDIENT_BLOCK]
- Pas d'icônes (✅). Liste simple.""",

    "inventory_mode_instruction": """Format : "- [Qté] [Ingrédient]".""",
    "direct_mode_instruction": """Format : "- [Qté] [Ingrédient]".""",
    "recipe_generation_user": "Plat: {dish_name}\nIngrédients: {products}\nÉcrivez la recette COMPLÈTE en Français.",
    "nutrition_instruction": "DE PLUS : Ajoutez '💪 **Nutrition :**'.",
    "freestyle_recipe": ".", "freestyle_recipe_user": ": {dish_name}",
    "ingredient_validation": ".", "ingredient_validation_user": ": {text}",
    "intent_detection": ".", "intent_detection_user": ": {message}",
}