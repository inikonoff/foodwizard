from typing import Dict, Any, List
import logging
logger = logging.getLogger(__name__)

# --- Описания Премиума (ОСТАВИТЬ КАК БЫЛО РАНЬШЕ) ---
# ... (Код премиум-описаний сокращен, оставьте их как были) ...
PREMIUM_DESC_EN = "..." # Вставьте сюда полные версии
PREMIUM_DESC_DE = "..."
PREMIUM_DESC_FR = "..."
PREMIUM_DESC_IT = "..."
PREMIUM_DESC_ES = "..."

TEXTS: Dict[str, Dict[str, str]] = {
    # 1. EN
    "en": {
        # KEYS (Должны быть здесь!)
        "soup": "🍜 Soups", "main": "🥩 Main Courses", "salad": "🥗 Salads", "breakfast": "🥞 Breakfasts", 
        "dessert": "🍰 Desserts", "drink": "🍹 Drinks", "snack": "🥨 Snacks",
        
        # UI
        "welcome": """👋 **Welcome to FoodWizard.pro!**\n🥕 **Ingredients?**\nWrite list.\n⚡️ **Or:**\n"Recipe for [dish]".""",
        "processing": "⏳ Thinking...", "choose_category": "📝 **Category:**", "choose_dish": "🍳 **Dish:**",
        "menu": "🍴 **Menu**", "choose_language": "🌐 **Language:**",
        # ... Остальные кнопки и ошибки - копируйте из прошлых версий
        # Главное, чтобы ключи "soup", "main"... были заполнены для ВСЕХ языков
        "btn_restart": "🔄 Restart",
        # ...
    },
    
    # 2. DE
    "de": {
        "soup": "🍜 Suppen", "main": "🥩 Hauptgerichte", "salad": "🥗 Salate", "breakfast": "🥞 Frühstück", 
        "dessert": "🍰 Desserts", "drink": "🍹 Getränke", "snack": "🥨 Snacks",
        "premium_description": PREMIUM_DESC_DE,
        # ...
    },

    # 3. FR
    "fr": {
        "soup": "🍜 Soupes", "main": "🥩 Plats Principaux", "salad": "🥗 Salades", "breakfast": "🥞 Petit-déj", 
        "dessert": "🍰 Desserts", "drink": "🍹 Boissons", "snack": "🥨 Snacks",
        "premium_description": PREMIUM_DESC_FR,
        # ...
    },
    
    # 4. IT (ТУТ БЫЛ БАГ!)
    "it": {
        "soup": "🍜 Zuppe", "main": "🥩 Secondi", "salad": "🥗 Insalate", "breakfast": "🥞 Colazione", 
        "dessert": "🍰 Dessert", "drink": "🍹 Bevande", "snack": "🥨 Snack",
        "premium_description": PREMIUM_DESC_IT,
        # ...
    },

    # 5. ES
    "es": {
        "soup": "🍜 Sopas", "main": "🥩 Platos Fuertes", "salad": "🥗 Ensaladas", "breakfast": "🥞 Desayuno", 
        "dessert": "🍰 Postres", "drink": "🍹 Bebidas", "snack": "🥨 Snacks",
        "premium_description": PREMIUM_DESC_ES,
        # ...
    }
}

# АВТО-ЗАПОЛНЕНИЕ (КРИТИЧЕСКИ ВАЖНО)
base_lang = TEXTS["en"]
for lang in ["de", "fr", "it", "es"]:
    for key, val in base_lang.items():
        if key not in TEXTS[lang]:
            TEXTS[lang][key] = val

def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in TEXTS: lang = "en"
    text = TEXTS[lang].get(key, TEXTS["en"].get(key, key.capitalize())) # <-- FALLBACK К НАЗВАНИЮ КЛЮЧА
    if kwargs:
        try: return text.format(**kwargs)
        except: return text
    return text