from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

class StateManager:
    def __init__(self):
        # Сессии пользователей
        self.user_sessions: Dict[int, dict] = {}
        # Время жизни сессии (часы)
        self.session_ttl_hours = 24
    
    def _cleanup_old_sessions(self):
        """Очищает старые сессии"""
        current_time = datetime.now()
        expired_users = []
        
        for user_id, session in self.user_sessions.items():
            last_activity = session.get('last_activity')
            if last_activity and (current_time - last_activity) > timedelta(hours=self.session_ttl_hours):
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.user_sessions[user_id]
    
    def _ensure_session(self, user_id: int) -> dict:
        """Создает или возвращает сессию пользователя"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'products': None,
                'categories': [],
                'generated_dishes': [],
                'current_dish': None,
                'last_activity': datetime.now(),
                'message_history': []
            }
        else:
            self.user_sessions[user_id]['last_activity'] = datetime.now()
        
        return self.user_sessions[user_id]
    
    # --- ПРОДУКТЫ ---
    def set_products(self, user_id: int, products: str):
        session = self._ensure_session(user_id)
        session['products'] = products
    
    def get_products(self, user_id: int) -> Optional[str]:
        session = self.user_sessions.get(user_id)
        return session.get('products') if session else None
    
    def append_products(self, user_id: int, new_products: str):
        current = self.get_products(user_id)
        if current:
            self.set_products(user_id, f"{current}, {new_products}")
        else:
            self.set_products(user_id, new_products)
    
    # --- КАТЕГОРИИ ---
    def set_categories(self, user_id: int, categories: List[str]):
        session = self._ensure_session(user_id)
        session['categories'] = categories
    
    def get_categories(self, user_id: int) -> List[str]:
        session = self.user_sessions.get(user_id)
        return session.get('categories', []) if session else []
    
    # --- БЛЮДА ---
    def set_generated_dishes(self, user_id: int, dishes: List[dict]):
        session = self._ensure_session(user_id)
        session['generated_dishes'] = dishes
    
    def get_generated_dishes(self, user_id: int) -> List[dict]:
        session = self.user_sessions.get(user_id)
        return session.get('generated_dishes', []) if session else []
    
    def get_generated_dish(self, user_id: int, index: int) -> Optional[str]:
        dishes = self.get_generated_dishes(user_id)
        if 0 <= index < len(dishes):
            return dishes[index].get('name')
        return None
    
    # --- ТЕКУЩЕЕ БЛЮДО ---
    def set_current_dish(self, user_id: int, dish_name: str):
        session = self._ensure_session(user_id)
        session['current_dish'] = dish_name
    
    def get_current_dish(self, user_id: int) -> Optional[str]:
        session = self.user_sessions.get(user_id)
        return session.get('current_dish') if session else None
    
    # --- ИСТОРИЯ СООБЩЕНИЙ ---
    def add_message_to_history(self, user_id: int, role: str, text: str, max_history: int = 10):
        session = self._ensure_session(user_id)
        
        if 'message_history' not in session:
            session['message_history'] = []
        
        session['message_history'].append({
            'role': role,
            'text': text,
            'timestamp': datetime.now().isoformat()
        })
        
        # Ограничиваем размер истории
        if len(session['message_history']) > max_history:
            session['message_history'] = session['message_history'][-max_history:]
    
    def get_message_history(self, user_id: int) -> List[dict]:
        session = self.user_sessions.get(user_id)
        return session.get('message_history', []) if session else []
    
    def get_last_bot_message(self, user_id: int) -> Optional[str]:
        history = self.get_message_history(user_id)
        for msg in reversed(history):
            if msg.get('role') == 'bot':
                return msg.get('text')
        return None
    
    # --- ОЧИСТКА СЕССИИ ---
    def clear_session(self, user_id: int):
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
    
    def clear_all_sessions(self):
        self.user_sessions.clear()
    
    # --- СТАТИСТИКА ---
    def get_active_sessions_count(self) -> int:
        self._cleanup_old_sessions()
        return len(self.user_sessions)
    
    def get_session_info(self, user_id: int) -> Optional[dict]:
        session = self.user_sessions.get(user_id)
        if session:
            return {
                'products': session.get('products'),
                'categories': session.get('categories'),
                'dishes_count': len(session.get('generated_dishes', [])),
                'current_dish': session.get('current_dish'),
                'last_activity': session.get('last_activity'),
                'history_count': len(session.get('message_history', []))
            }
        return None

# Глобальный экземпляр StateManager
state_manager = StateManager()
