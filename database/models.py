from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class UserLanguage(str, Enum):
    """®¤¤¥à¦¨¢ ¥¬ë¥ ï§ëª¨"""
    RU = "ru"
    EN = "en"
    DE = "de"
    FR = "fr"
    IT = "it"
    ES = "es"

class Category(str, Enum):
    """Š â¥£®à¨¨ ¡«î¤"""
    SOUP = "soup"
    MAIN = "main"
    SALAD = "salad"
    BREAKFAST = "breakfast"
    DESSERT = "dessert"
    DRINK = "drink"
    SNACK = "snack"

class UserBase(BaseModel):
    """ §®¢ ï ¬®¤¥«ì ¯®«ì§®¢ â¥«ï"""
    user_id: int = Field(..., description="ID ¯®«ì§®¢ â¥«ï ¢ Telegram")
    first_name: str
    username: Optional[str] = None
    language_code: UserLanguage = UserLanguage.RU
    is_premium: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    last_active_at: datetime = Field(default_factory=datetime.now)

class FavoriteRecipe(BaseModel):
    """Œ®¤¥«ì ¨§¡à ­­®£® à¥æ¥¯â """
    id: Optional[int] = None
    user_id: int = Field(..., description="ID ¯®«ì§®¢ â¥«ï")
    dish_name: str = Field(..., description=" §¢ ­¨¥ ¡«î¤ ")
    recipe_text: str = Field(..., description="’¥ªáâ à¥æ¥¯â ")
    category: Optional[Category] = None
    ingredients: Optional[str] = None
    language: UserLanguage = UserLanguage.RU
    created_at: datetime = Field(default_factory=datetime.now)

class GroqCacheItem(BaseModel):
    """Œ®¤¥«ì í«¥¬¥­â  ªíè  Groq"""
    hash: str = Field(..., description="•¥è § ¯à®á ")
    response: str = Field(..., description="Žâ¢¥â ®â Groq")
    language: UserLanguage
    model: str = Field(..., description="Œ®¤¥«ì Groq")
    tokens_used: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(..., description="‚à¥¬ï ¨áâ¥ç¥­¨ï ªíè ")

class MetricEvent(BaseModel):
    """Œ®¤¥«ì á®¡ëâ¨ï ¤«ï ¬¥âà¨ª"""
    id: Optional[int] = None
    user_id: int
    event_type: str = Field(..., description="’¨¯ á®¡ëâ¨ï")
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

class Dish(BaseModel):
    """Œ®¤¥«ì ¡«î¤ """
    name: str = Field(..., description=" §¢ ­¨¥ ¡«î¤ ")
    desc: str = Field(..., description="Ž¯¨á ­¨¥ ¡«î¤ ")

class RecipeRequest(BaseModel):
    """Œ®¤¥«ì § ¯à®á  ­  £¥­¥à æ¨î à¥æ¥¯â """
    dish_name: str
    products: str
    language: UserLanguage = UserLanguage.RU
    category: Optional[Category] = None

class IntentAnalysis(BaseModel):
    """Œ®¤¥«ì  ­ «¨§  ­ ¬¥à¥­¨ï ¯®«ì§®¢ â¥«ï"""
    intent: str = Field(..., description=" ¬¥à¥­¨¥: add_products, select_dish, unclear")
    products: str = Field("", description="Ž¡­ àã¦¥­­ë¥ ¯à®¤ãªâë")
    dish_name: str = Field("", description="Ž¡­ àã¦¥­­®¥ ­ §¢ ­¨¥ ¡«î¤ ")
