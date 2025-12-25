from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

# --- ЯЗЫКИ ---
class UserLanguage(str, Enum):
    RU = "ru"
    EN = "en"
    DE = "de"
    FR = "fr"
    IT = "it"
    ES = "es"

# --- КАТЕГОРИИ БЛЮД ---
class Category(str, Enum):
    SOUP = "soup"
    MAIN = "main"
    SALAD = "salad"
    BREAKFAST = "breakfast"
    DESSERT = "dessert"
    DRINK = "drink"
    SNACK = "snack"
    UNKNOWN = "unknown"

# --- МОДЕЛИ ПОЛЬЗОВАТЕЛЕЙ (ВОТ ЧЕГО НЕ ХВАТАЛО) ---
class UserBase(BaseModel):
    user_id: int
    first_name: str
    username: Optional[str] = None
    language_code: str = "en"
    is_premium: bool = False

# --- МОДЕЛИ РЕЦЕПТОВ ---
class FavoriteRecipe(BaseModel):
    user_id: int
    dish_name: str
    recipe_text: str
    ingredients: Optional[str] = None
    language: str = "en"
    category: Optional[Category] = None
    created_at: Optional[datetime] = None