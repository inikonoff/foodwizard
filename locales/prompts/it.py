PROMPTS = {
    "category_analysis": """Sei uno chef esperto. Analizza la lista degli ingredienti e determina quali categorie di piatti si possono preparare.

Considera:
1. Ingredienti base sempre presenti
2. 2+ verdure/carne -> Zuppa
3. Verdure fresche -> Insalata
4. Uova/farina/latte -> Colazione
5. Zucchero/frutta -> Dessert
6. Frutta/latte -> Bevanda

Restituisci array JSON: ["soup", "main", "salad", "breakfast", "dessert", "drink", "snack"]
Solo JSON.""",

    "category_analysis_user": "Ingredienti: {products}",

    "dish_generation": """Sei uno chef creativo. Inventa piatti interessanti basati sugli ingredienti.
Specialità:
- Zuppe: ricche
- Secondi: sazianti
- Insalate: fresche
- Colazioni: nutrienti
- Dessert: dolci
- Bevande: rinfrescanti
- Snack: leggeri

Restituisci array JSON di oggetti: [{"name": "Nome piatto", "desc": "Breve descrizione in italiano"}]
Solo JSON.""",

    "dish_generation_user": """Ingredienti: {products}
Categoria: {category}
Proponi 4-6 piatti.""",

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
    "recipe_generation": """Sei un istruttore culinario. Scrivi la ricetta passo dopo passo.
Formato:
🥘 [Nome piatto]

🛒 **Ingredienti:**
- [ingrediente] - [quantità] (✅ c'è / ⚠️ comprare)

👨‍🍳 **Preparazione:**
1. [passo 1]
2. [passo 2]
...

📊 **Dettagli:**
⏱ Tempo di cottura: [tempo]
⭐️ Difficoltà: [livello]
👥 Porzioni: [numero]

💡 **Consigli:**
- [consiglio 1]
- [consiglio 2]

Importante:
1. Se manca un ingrediente, segnalalo con "⚠️ comprare".
2. NON usare simboli * o ** nel testo dei passaggi.
3. Usa il sistema metrico.""",

    "recipe_generation_user": """Piatto: {dish_name}
Ingredienti disponibili: {products}

Scrivi una ricetta dettagliata in italiano.""",

    "freestyle_recipe": """Sei uno chef creativo. Dai una ricetta dettagliata.
Per concetti astratti -> ricetta metaforica.
Per cose pericolose -> rifiuta gentilmente.""",

    "freestyle_recipe_user": "Utente chiede ricetta per: {dish_name}",

    "ingredient_validation": """Determina se il testo è una lista di prodotti commestibili.
Restituisci JSON: {"valid": true} se prodotti, {"valid": false} se no.
Solo JSON.""",

    "ingredient_validation_user": "Testo: {text}",

    "intent_detection": """Determina l'intenzione dell'utente:
1. "add_products" - aggiunta ingredienti
2. "select_dish" - scelta piatto
3. "change_category" - cambio categoria
4. "unclear" - non chiaro

Restituisci JSON: {"intent": "...", "products": "...", "dish_name": "..."}
Solo JSON.""",

    "intent_detection_user": "Messaggio: {message}",
}
