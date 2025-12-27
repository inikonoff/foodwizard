from .texts import get_text
from .prompts import get_prompt

# get_all_prompts убираем, так как мы её не писали и она не нужна для работы бота
__all__ = ['get_text', 'get_prompt']