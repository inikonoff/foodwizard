async def handle_text_message(message: Message):
    # ...
    try:
        # ... analyze ...
        categories = analysis_result["categories"] # Получили список от Groq
        # ...

        builder = InlineKeyboardBuilder()
        valid_count = 0
        for category in categories:
            # 1. Берем ключ от Groq, приводим к нижнему регистру и стрипим
            clean_key = category.lower().strip()
            
            # 2. Ищем перевод
            label = get_text(lang, clean_key)
            
            # 3. Если перевода нет (get_text вернул сам ключ из fallback) - используем красиво
            if label == clean_key or not label:
                 label = clean_key.title() # "main" -> "Main"

            builder.row(InlineKeyboardButton(text=label, callback_data=f"cat_{clean_key}"))
            valid_count += 1
                
        if valid_count == 0:
            # ... error