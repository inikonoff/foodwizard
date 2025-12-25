from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

# Перечисление языков
class UserLanguage(str, Enum):
    RU = "ru"
    EN = "en"
    DE = "de"
    FR = "fr"
    IT = "it"
    ES = "es"

# Перечисление категорий (Важно для favorites.py)
class Category(str, Enum):
    SOUP = "soup"
    MAIN = "main"
    SALAD = "salad"
    BREAKFAST = "breakfast"
    DESSERT = "dessert"
    DRINK = "drink"
    SNACK = "snack"
    UNKNOWN = "unknown"

# Модель для избранного рецепта
class FavoriteRecipe(BaseModel):
    user_id: int
    dish_name: str
    recipe_text: str
    ingredients: Optional[str] = None
    language: str = "en"
    category: Optional[Category] = None
    created_at: Optional[datetime] = None