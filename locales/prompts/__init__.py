import os
import json
from typing import Dict, Any
import importlib

# Динамически загружаем все промпты
PROMPTS: Dict[str, Dict[str, str]] = {}

# Языки, которые мы поддерживаем
LANGUAGES = ["ru", "en", "de", "fr", "it", "es"]

# Загружаем промпты для каждого языка
for lang in LANGUAGES:
    try:
        # Пытаемся импортировать модуль locales.prompts.<lang> (например, locales.prompts.ru)
        module_name = f"locales.prompts.{lang}"
        module = importlib.import_module(module_name)
        PROMPTS[lang] = getattr(module, "PROMPTS", {})
    except ImportError:
        print(f"?? Промпты для языка '{lang}' не найдены. Пропускаем.")
        PROMPTS[lang] = {}

def get_prompt(lang: str, prompt_name: str, **kwargs) -> str:
    """Получает промпт для указанного языка с подстановкой переменных"""
    # Если язык не поддерживается, используем русский как fallback
    if lang not in PROMPTS:
        lang = "ru"
    
    prompts_for_lang = PROMPTS.get(lang, PROMPTS["ru"])
    prompt = prompts_for_lang.get(prompt_name, "")
    
    if not prompt and lang != "ru":
        # Fallback на русский, если промпт не найден
        prompt = PROMPTS["ru"].get(prompt_name, "")
    
    # Подставляем переменные, если они есть
    if kwargs and prompt:
        try:
            return prompt.format(**kwargs)
        except KeyError:
            # Если промпт не содержит всех ключей, возвращаем как есть
            return prompt
    
    return prompt

def get_all_prompts() -> Dict[str, Dict[str, str]]:
    """Возвращает весь словарь промптов для всех языков (НОВАЯ ФУНКЦИЯ)"""
    return PROMPTS
