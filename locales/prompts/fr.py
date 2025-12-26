PROMPTS = {
    "category_analysis": """Vous êtes un chef expérimenté.
Analysez les ingrédients.

IMPORTANT : Utilisez EXACTEMENT les clés anglaises ci-dessous. NE PAS traduire les clés.
Allowed Keys: "soup", "main", "salad", "breakfast", "dessert", "drink", "snack".

Retournez un objet JSON :
{
  "categories": ["soup", "main"],
  "suggestion": "💡 Conseil : Ajoutez [Ingrédient] pour faire [Plat] !"
}
Uniquement JSON.""",

    "category_analysis_user": "Ingrédients : {products}",

    "dish_generation": """Chef créatif. Suggérez des plats.
Tableau JSON : [{"name": "Nom du plat", "desc": "Brève description en français"}]
Uniquement JSON.""",

    "dish_generation_user": "Ingrédients : {products}\nCatégorie : {category}\nProposez 4-6 plats.",

    "recipe_generation": """Instructeur culinaire. Écrivez la recette en français.

Format :
🥘 [Nom du plat]

🛒 **Ingrédients :**
[INGREDIENT_BLOCK]

👨‍🍳 **Préparation :**
1. [étape 1]
...

📊 **Détails :**
⏱ Temps : [temps]
⭐️ Difficulté : [niveau]
👥 Portions : [nombre]

💡 **Conseils :**
- [conseil]""",

    "inventory_mode_instruction": """
Marquez le statut :
- [ingrédient] - [quantité] (✅ dispo / ⚠️ acheter)
(Eau, sel, huile sont toujours ✅ dispo).""",
    
    "direct_mode_instruction": """
Listez simplement :
- [ingrédient] - [quantité]
NE PAS utiliser d'icônes de statut.""",

    "recipe_generation_user": "Plat: {dish_name}\nIngrédients: {products}\nÉcrivez la recette en français.",
    
    "nutrition_instruction": "DE PLUS : Ajoutez la section '💪 **Nutrition (par portion) :**' (Calories, Macros).",

    "freestyle_recipe": "Chef créatif.", "freestyle_recipe_user": "Demande : {dish_name}",
    "ingredient_validation": "Comestible? JSON: {'valid': true/false}", "ingredient_validation_user": "Texte : {text}",
    "intent_detection": "Intent? JSON: {'intent': ...}", "intent_detection_user": "Message : {message}",
}