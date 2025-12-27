# ... (основной код из предыдущего ответа) ...
# Обновляем только одну функцию:

async def handle_favorite_pagination(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = (await users_repo.get_user(user_id)).get('language_code', 'en')
    
    # 1. Попытка парсинга страницы
    page = 1
    if callback.data:
        parts = callback.data.split('_')
        # Если data = "show_favorites" (кнопка меню), split даст 2 элемента
        # Если data = "fav_page_2" (пагинация), split даст 3 элемента (индекс 2 - номер)
        if len(parts) >= 3 and parts[2].isdigit():
            page = int(parts[2])
    
    favorites, total_pages = await favorites_repo.get_favorites_page(user_id, page)
    
    # Если на запрошенной странице пусто (удаляли рецепты) - грузим 1-ю страницу
    if not favorites and page > 1:
        page = 1
        favorites, total_pages = await favorites_repo.get_favorites_page(user_id, 1)
        
    if not favorites:
        try: await callback.message.edit_text(get_text(lang, "favorites_empty"))
        except: await callback.message.answer(get_text(lang, "favorites_empty"))
        return 
    
    # ... (дальше сборка клавиатуры как была раньше) ...
    # Я копирую этот код сюда для полноты файла, замените старый:
    header = get_text(lang, "favorites_title") + f" ({page}/{total_pages})"
    # Удаляем ** из заголовка для красоты
    header = header.replace("**", "")
    header = f"<b>{header}</b>"
    
    builder = InlineKeyboardBuilder()
    for fav in favorites:
        date_str = fav['created_at'].strftime("%d.%m")
        btn_text = f"{fav['dish_name']} ({date_str})"
        builder.row(InlineKeyboardButton(text=btn_text, callback_data=f"view_fav_{fav['id']}"))
    
    if total_pages > 1:
        row = []
        if page > 1: row.append(InlineKeyboardButton(text="⬅️", callback_data=f"fav_page_{page - 1}"))
        row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages: row.append(InlineKeyboardButton(text="➡️", callback_data=f"fav_page_{page + 1}"))
        builder.row(*row)
    
    builder.row(InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu"))
    
    try:
        await callback.message.edit_text(header, reply_markup=builder.as_markup(), parse_mode="HTML")
    except:
        await callback.message.answer(header, reply_markup=builder.as_markup(), parse_mode="HTML")
    
    await callback.answer()
    await track_safely(user_id, "favorites_page_viewed", {"page": page})

# ... (Остальной файл handlers/favorites.py остается прежним) ...
