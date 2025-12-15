from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class UserLanguage(str, Enum):
    """Поддерживаемые языки"""
    RU = "ru"
    EN = "en"
    DE = "de"
    FR = "fr"
    IT = "it"
    ES = "es"

class Category(str, Enum):
    """Категории блюд"""
    SOUP = "soup"
    MAIN = "main"
    SALAD = "salad"
    BREAKFAST = "breakfast"
    DESSERT = "dessert"
    DRINK = "drink"
    SNACK = "snack"

class UserBase(BaseModel):
    """Базовая модель пользователя"""
    user_id: int = Field(..., description="ID пользователя в Telegram")
    first_name: str
    username: Optional[str] = None
    language_code: UserLanguage = UserLanguage.RU
    is_premium: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    last_active_at: datetime = Field(default_factory=datetime.now)

class FavoriteRecipe(BaseModel):
    """Модель избранного рецепта"""
    id: Optional[int] = None
    user_id: int = Field(..., description="ID пользователя")
    dish_name: str = Field(..., description="Название блюда")
    recipe_text: str = Field(..., description="Текст рецепта")
    category: Optional[Category] = None
    ingredients: Optional[str] = None
    language: UserLanguage = UserLanguage.RU
    created_at: datetime = Field(default_factory=datetime.now)

class GroqCacheItem(BaseModel):
    """Модель элемента кэша Groq"""
    hash: str = Field(..., description="Хеш запроса")
    response: str = Field(..., description="Ответ от Groq")
    language: UserLanguage
    model: str = Field(..., description="Модель Groq")
    tokens_used: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(..., description="Время истечения кэша")

class MetricEvent(BaseModel):
    """Модель события для метрик"""
    id: Optional[int] = None
    user_id: int
    event_type: str = Field(..., description="Тип события")
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

class Dish(BaseModel):
    """Модель блюда"""
    name: str = Field(..., description="Название блюда")
    desc: str = Field(..., description="Описание блюда")

class RecipeRequest(BaseModel):
    """Модель запроса на генерацию рецепта"""
    dish_name: str
    products: str
    language: UserLanguage = UserLanguage.RU
    category: Optional[Category] = None

class IntentAnalysis(BaseModel):
    """Модель анализа намерения пользователя"""
    intent: str = Field(..., description="Намерение: add_products, select_dish, unclear")
    products: str = Field("", description="Обнаруженные продукты")
    dish_name: str = Field("", description="Обнаруженное название блюда")