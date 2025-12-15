import os
import json
from typing import Dict, Any
import importlib

# „¨­ ¬¨ç¥áª¨ § £àã¦ ¥¬ ¢á¥ ¯à®¬¯âë
PROMPTS: Dict[str, Dict[str, str]] = {}

# Ÿ§ëª¨, ª®â®àë¥ ¬ë ¯®¤¤¥à¦¨¢ ¥¬
LANGUAGES = ["ru", "en", "de", "fr", "it", "es"]

# ‡ £àã¦ ¥¬ ¯à®¬¯âë ¤«ï ª ¦¤®£® ï§ëª 
for lang in LANGUAGES:
    try:
        module_name = f"locales.prompts.{lang}"
        module = importlib.import_module(module_name)
        PROMPTS[lang] = getattr(module, "PROMPTS", {})
    except ImportError:
        print(f"?? à®¬¯âë ¤«ï ï§ëª  '{lang}' ­¥ ­ ©¤¥­ë. à®¯ãáª ¥¬.")
        PROMPTS[lang] = {}

def get_prompt(lang: str, prompt_name: str, **kwargs) -> str:
    """®«ãç ¥â ¯à®¬¯â ¤«ï ãª § ­­®£® ï§ëª  á ¯®¤áâ ­®¢ª®© ¯¥à¥¬¥­­ëå"""
    # …á«¨ ï§ëª ­¥ ¯®¤¤¥à¦¨¢ ¥âáï, ¨á¯®«ì§ã¥¬ àãááª¨© ª ª fallback
    if lang not in PROMPTS:
        lang = "ru"
    
    prompts_for_lang = PROMPTS.get(lang, PROMPTS["ru"])
    prompt = prompts_for_lang.get(prompt_name, "")
    
    if not prompt and lang != "ru":
        # Fallback ­  àãááª¨©, ¥á«¨ ¯à®¬¯â ­¥ ­ ©¤¥­
        prompt = PROMPTS["ru"].get(prompt_name, "")
    
    # ®¤áâ ¢«ï¥¬ ¯¥à¥¬¥­­ë¥, ¥á«¨ ®­¨ ¥áâì
    if kwargs and prompt:
        try:
            return prompt.format(**kwargs)
        except KeyError as e:
            print(f"?? Žè¨¡ª  ¯®¤áâ ­®¢ª¨ ¯¥à¥¬¥­­®© {e} ¢ ¯à®¬¯â¥ {prompt_name}")
            return prompt
    
    return prompt

def get_all_prompts(lang: str) -> Dict[str, str]:
    """‚®§¢à é ¥â ¢á¥ ¯à®¬¯âë ¤«ï ãª § ­­®£® ï§ëª """
    return PROMPTS.get(lang, PROMPTS["ru"])
