from typing import Dict

# Здесь вставь все PROMPTS из твоих ru.py, en.py и т.д.
PROMPTS: Dict[str, Dict[str, str]] = {
    "ru": { ... весь словарь из ru.py ... },
    "en": { ... },
    # и т.д.
}

def get_prompt(lang: str, key: str) -> str:
    return PROMPTS.get(lang, PROMPTS["ru"]).get(key, "")
