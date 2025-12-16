import os
import json
from typing import Dict, Any
import importlib

# Динамически загружаем все промпты
PROMPTS: Dict[str, Dict[str, str]] = {}

# Языки, которые мы поддерживаем
# Берем из config или явно задаем
LANGUAGES = ["ru", "en", "de", "fr", "it", "es"] 

# Загружаем промпты для каждого языка
for lang in LANGUAGES:
    try:
        # Для динамического импорта из подпапки 'locales.prompts'
        # Пакет 'locales.prompts' должен быть доступен
        module = importlib.import_module(f".{lang}", package="locales.prompts") 
        PROMPTS[lang] = getattr(module, "PROMPTS", {})
    except ImportError:
        # Если промпты для языка не найдены (например, locales/prompts/de.py нет)
        # Это не критично, но нужно об этом знать
        print(f"⚠️ Промпты для языка '{lang}' не найдены. Пропускаем.")
        PROMPTS[lang] = {}

def get_prompt(lang: str, prompt_name: str, **kwargs) -> str:
    """Получает промпт для указанного языка с подстановкой переменных"""
    # Если язык не поддерживается, используем русский как fallback
    if lang not in PROMPTS:
        lang = "ru"
    
    prompts_for_lang = PROMPTS.get(lang, PROMPTS["ru"])
    # Сначала ищем промпт в выбранном языке
    prompt = prompts_for_lang.get(prompt_name, "")
    
    if not prompt and lang != "ru":
        # Fallback на русский, если промпт не найден в текущем языке
        prompt = PROMPTS["ru"].get(prompt_name, "")
    
    # Подставляем переменные, если они есть
    if kwargs and prompt:
        try:
            return prompt.format(**kwargs)
        except KeyError as e:
            # Ошибка, если в промпте есть {ключ}, но он не передан
            print(f"❌ Ошибка форматирования промпта '{prompt_name}' для языка '{lang}'. Не передан ключ: {e}")
            return prompt # Возвращаем неформатированный промпт
        except IndexError:
             # На всякий случай
             return prompt
             
    return prompt
