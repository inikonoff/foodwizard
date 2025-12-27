from typing import Dict, Any

# 1. Импортируем словари из соседних файлов
# Если какого-то файла не будет, бот не упадет, а создаст пустой словарь
try: from .en import PROMPTS as en_prompts
except ImportError: en_prompts = {}

try: from .de import PROMPTS as de_prompts
except ImportError: de_prompts = {}

try: from .fr import PROMPTS as fr_prompts
except ImportError: fr_prompts = {}

try: from .it import PROMPTS as it_prompts
except ImportError: it_prompts = {}

try: from .es import PROMPTS as es_prompts
except ImportError: es_prompts = {}

# 2. Собираем единый реестр
PROMPTS_REGISTRY = {
    "en": en_prompts,
    "de": de_prompts,
    "fr": fr_prompts,
    "it": it_prompts,
    "es": es_prompts,
}

# 3. Главная функция
def get_prompt(lang: str, key: str) -> str:
    """Получает текст промпта с безопасным фоллбэком на Английский."""
    # Если язык не поддерживается, берем EN
    if lang not in PROMPTS_REGISTRY:
        lang = "en"
        
    current_dict = PROMPTS_REGISTRY.get(lang)
    
    # Если словарь пустой (файл не создали) -> берем EN
    if not current_dict:
        current_dict = PROMPTS_REGISTRY["en"]
        
    # Пробуем достать ключ
    val = current_dict.get(key)
    
    # Если ключа нет в текущем языке -> берем из EN
    if not val:
        val = PROMPTS_REGISTRY["en"].get(key, "")
        
    return val