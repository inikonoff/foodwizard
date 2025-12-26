PROMPTS = {
    "category_analysis": """Sei uno chef esperto.
Analizza gli ingredienti.

IMPORTANTE: Restituisci ESATTAMENTE le chiavi inglesi elencate di seguito. NON tradurre le chiavi.
Allowed Keys: "soup", "main", "salad", "breakfast", "dessert", "drink", "snack".

Restituisci oggetto JSON:
{
  "categories": ["soup", "main"],
  "suggestion": "💡 Consiglio: Aggiungi [Ingrediente] per fare [Piatto]!"
}
Solo JSON.""",

    "category_analysis_user": "Ingredienti: {products}",

    "dish_generation": """Chef creativo. Suggerisci piatti.
Array JSON: [{"name": "Nome", "desc": "Descrizione in italiano"}]
Solo JSON.""",

    "dish_generation_user": "Ingredienti: {products}\nCategoria: {category}\nProponi 4-6 piatti.",

    "recipe_generation": """Istruttore culinario. Scrivi la ricetta in italiano.

Formato:
🥘 [Nome]

🛒 **Ingredienti:**
[INGREDIENT_BLOCK]

👨‍🍳 **Preparazione:**
1. [passo 1]
...

📊 **Dettagli:**
⏱ Tempo: [tempo]
⭐️ Difficoltà: [livello]
👥 Porzioni: [numero]

💡 **Consigli:**
- [consiglio]""",

    "inventory_mode_instruction": """
Stato ingredienti:
- [ingrediente] - [quantità] (✅ c'è / ⚠️ comprare)
(Acqua, sale, olio sono sempre ✅).""",
    
    "direct_mode_instruction": """
Elenco semplice:
- [ingrediente] - [quantità]
NON usare icone di stato.""",

    "recipe_generation_user": "Piatto: {dish_name}\nIngredienti: {products}\nScrivi la ricetta in italiano.",
    
    "nutrition_instruction": "INOLTRE: Aggiungi sezione '💪 **Valori nutrizionali (per porzione):**' (Calorie, Macro).",

    "freestyle_recipe": "Chef creativo.", "freestyle_recipe_user": "Richiesta: {dish_name}",
    "ingredient_validation": "Commestibile? JSON: {'valid': true/false}", "ingredient_validation_user": "Testo: {text}",
    "intent_detection": "Intent? JSON: {'intent': ...}", "intent_detection_user": "Messaggio: {message}",
}