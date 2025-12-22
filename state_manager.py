from typing import Dict, Any, Optional, List
from datetime import datetime

class StateManager:
    """
    Простое хранилище состояния в памяти для каждого пользователя.
    """
    def __init__(self):
        self.user_states: Dict[int, Dict[str, Any]] = {} 

    def set_products(self, user_id: int, products: str):
        """Устанавливает новый список продуктов, очищая старое состояние."""
        if user_id not in self.user_states:
             self.user_states[user_id] = {}
        
        # Очищаем старое состояние
        self.user_states[user_id].clear() 
        
        self.user_states[user_id]['products'] = products
        self.user_states[user_id]['timestamp'] = datetime.now()

    def get_products(self, user_id: int) -> Optional[str]:
        return self.user_states.get(user_id, {}).get('products')

    def set_categories(self, user_id: int, categories: List[str]):
        if user_id in self.user_states:
             self.user_states[user_id]['categories'] = categories
             
    def get_categories(self, user_id: int) -> Optional[List[str]]:
        return self.user_states.get(user_id, {}).get('categories')

    def set_generated_dishes(self, user_id: int, dishes: List[Dict]):
        if user_id in self.user_states:
             self.user_states[user_id]['generated_dishes'] = dishes

    def get_generated_dishes(self, user_id: int) -> Optional[List[Dict]]:
        return self.user_states.get(user_id, {}).get('generated_dishes')

    def set_current_dish(self, user_id: int, dish: Dict):
        if user_id in self.user_states:
             self.user_states[user_id]['current_dish'] = dish

    # !!! ДОБАВЛЕН НЕДОСТАЮЩИЙ МЕТОД !!!
    def get_current_dish(self, user_id: int) -> Optional[Dict]:
        """Получает текущее выбранное блюдо."""
        return self.user_states.get(user_id, {}).get('current_dish')

state_manager = StateManager()
