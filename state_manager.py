from typing import Dict, Any, Optional, List
from datetime import datetime # <--- ИСПРАВЛЕНО: Добавлен необходимый импорт!

class StateManager:
    """
    Простое хранилище состояния в памяти для каждого пользователя.
    
    ВНИМАНИЕ: Это In-Memory решение. Не подходит для продакшена/масштабирования.
    Должно быть заменено на Redis/PostgreSQL.
    """
    def __init__(self):
        # Инициализируем словарь для хранения состояния
        self.user_states: Dict[int, Dict[str, Any]] = {} 

    def set_products(self, user_id: int, products: str):
        """Устанавливает новый список продуктов, очищая старое состояние."""
        # Гарантируем, что запись для пользователя существует
        if user_id not in self.user_states:
             self.user_states[user_id] = {}
        
        # Очищаем старое состояние, чтобы начать новый флоу
        self.user_states[user_id].clear() 
        
        self.user_states[user_id]['products'] = products
        self.user_states[user_id]['timestamp'] = datetime.now() # <-- Теперь datetime определен!

    def get_products(self, user_id: int) -> Optional[str]:
        """Безопасно получает продукты из состояния."""
        return self.user_states.get(user_id, {}).get('products')

    def set_categories(self, user_id: int, categories: List[str]):
        """Устанавливает список категорий."""
        if user_id in self.user_states:
             self.user_states[user_id]['categories'] = categories
             
    def get_categories(self, user_id: int) -> Optional[List[str]]:
        """Безопасно получает категории из состояния."""
        return self.user_states.get(user_id, {}).get('categories')

    def set_generated_dishes(self, user_id: int, dishes: List[Dict]):
        """Устанавливает список сгенерированных блюд."""
        if user_id in self.user_states:
             self.user_states[user_id]['generated_dishes'] = dishes

    def get_generated_dishes(self, user_id: int) -> Optional[List[Dict]]:
        """Безопасно получает список сгенерированных блюд."""
        return self.user_states.get(user_id, {}).get('generated_dishes')

    def set_current_dish(self, user_id: int, dish: Dict):
        """Устанавливает выбранное блюдо."""
        if user_id in self.user_states:
             self.user_states[user_id]['current_dish'] = dish

# Инициализируем один глобальный экземпляр
state_manager = StateManager()