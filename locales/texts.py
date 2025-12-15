from typing import Dict, Any

TEXTS: Dict[str, Dict[str, str]] = {
    "ru": {
        # Интерфейс
        "welcome": "?? Привет, {name}!\n\nЯ бот-шеф. Назови продукты, а я скажу, что из них приготовить.",
        "start_manual": "?? **Отправьте голосовое или текстовое сообщение** с продуктами.\n?? Или напишите **\"Дай рецепт [блюдо]\"**.",
        "processing": "????? Думаю...",
        "menu": "?? **Что будем готовить?**",
        "choose_language": "?? **Выберите язык:**",
        
        # Категории
        "soup": "?? Супы",
        "main": "?? Вторые блюда",
        "salad": "?? Салаты",
        "breakfast": "?? Завтраки",
        "dessert": "?? Десерты",
        "drink": "?? Напитки",
        "snack": "?? Закуски",
        
        # Кнопки
        "btn_favorites": "? Избранное",
        "btn_restart": "?? Рестарт",
        "btn_change_lang": "?? Сменить язык",
        "btn_help": "????? Помощь",
        "btn_add_to_fav": "? Добавить в избранное",
        "btn_remove_from_fav": "? В избранном",
        "btn_back": "?? Назад",
        "btn_next": "Вперед ??",
        "btn_prev": "?? Назад",
        "btn_hide": "?? Скрыть",
        "btn_another": "?? Другой вариант",
        "btn_to_categories": "?? К категориям",
        
        # Избранное
        "favorites_empty": "? У вас пока нет избранных рецептов.",
        "favorites_list": "? **Избранное** (стр. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. **{dish}**\n   ?? {date}\n",
        "recipe_added_to_fav": "? Рецепт добавлен в избранное!",
        "recipe_removed_from_fav": "??? Рецепт удалён из избранного.",
        
        # Ошибки
        "error_voice": "?? Не удалось распознать голос. Попробуйте ещё раз.",
        "error_generation": "? Ошибка генерации. Попробуйте снова.",
        "error_no_products": "?? Не вижу продуктов. Попробуйте: <морковь, лук, картошка>.",
        "error_too_long": "?? Слишком длинное сообщение. Максимум 1000 символов.",
        
        # Успех
        "products_accepted": "? Продукты приняты: {products}",
        "products_added": "? Добавлено: {products}",
        "choose_category": "?? **Выберите категорию:**",
        "choose_dish": "?? **Выберите блюдо:**",
        
        # Языки
        "lang_changed": "?? Язык изменён на русский.",
        "lang_ru": "???? Русский",
        "lang_en": "???? English",
        "lang_de": "???? Deutsch",
        "lang_fr": "???? Francais",
        "lang_it": "???? Italiano",
        "lang_es": "???? Espanol",
        
        # Помощь
        "help_title": "????? **Помощь по боту-шефу**",
        "help_text": """
*Как пользоваться:*
1. Отправьте продукты (текстом или голосом)
2. Выберите категорию блюд
3. Выберите блюдо из списка
4. Получите рецепт

*Команды:*
/start - начать заново
/favorites - избранные рецепты
/lang - сменить язык
/help - помощь

*Советы:*
- Можно добавлять продукты несколько раз
- Нажмите ? под рецептом, чтобы сохранить
- Голосовые сообщения автоматически удаляются

*Поддержка:* @support
        """,
        
        # Пасхалки
        "thanks": "На здоровье! ?????",
        "easter_egg": "?? Вы нашли пасхалку!",
    },
    
    "en": {
        "welcome": "?? Hello, {name}!\n\nI'm a chef bot. Name the ingredients, and I'll tell you what to cook.",
        "start_manual": "?? **Send a voice or text message** with ingredients.\n?? Or type **\"Recipe for [dish]\"**.",
        "processing": "????? Thinking...",
        "menu": "?? **What shall we cook?**",
        "choose_language": "?? **Choose language:**",
        
        "soup": "?? Soups",
        "main": "?? Main Course",
        "salad": "?? Salads",
        "breakfast": "?? Breakfast",
        "dessert": "?? Desserts",
        "drink": "?? Drinks",
        "snack": "?? Snacks",
        
        "btn_favorites": "? Favorites",
        "btn_restart": "?? Restart",
        "btn_change_lang": "?? Change language",
        "btn_help": "????? Help",
        "btn_add_to_fav": "? Add to favorites",
        "btn_remove_from_fav": "? In favorites",
        "btn_back": "?? Back",
        "btn_next": "Next ??",
        "btn_prev": "?? Prev",
        "btn_hide": "?? Hide",
        "btn_another": "?? Another variant",
        "btn_to_categories": "?? To categories",
        
        "favorites_empty": "? You don't have any favorite recipes yet.",
        "favorites_list": "? **Favorites** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. **{dish}**\n   ?? {date}\n",
        "recipe_added_to_fav": "? Recipe added to favorites!",
        "recipe_removed_from_fav": "??? Recipe removed from favorites.",
        
        "error_voice": "?? Couldn't recognize voice. Please try again.",
        "error_generation": "? Generation error. Please try again.",
        "error_no_products": "?? I don't see any products. Try: 'carrots, onions, potatoes'.",
        "error_too_long": "?? Message too long. Maximum 1000 characters.",
        
        "products_accepted": "? Products accepted: {products}",
        "products_added": "? Added: {products}",
        "choose_category": "?? **Choose category:**",
        "choose_dish": "?? **Choose a dish:**",
        
        "lang_changed": "?? Language changed to English.",
        "lang_ru": "???? Русский",
        "lang_en": "???? English",
        "lang_de": "???? Deutsch",
        "lang_fr": "???? Francais",
        "lang_it": "???? Italiano",
        "lang_es": "???? Espanol",
        
        "help_title": "????? **Chef Bot Help**",
        "help_text": """
*How to use:*
1. Send ingredients (text or voice)
2. Choose dish category
3. Choose dish from list
4. Get recipe

*Commands:*
/start - start over
/favorites - favorite recipes
/lang - change language
/help - help

*Tips:*
- You can add ingredients multiple times
- Click ? under recipe to save
- Voice messages are automatically deleted

*Support:* @support
        """,
        
        "thanks": "You're welcome! ?????",
        "easter_egg": "?? You found an easter egg!",
    },
    
    "de": {
        "welcome": "?? Hallo, {name}!\n\nIch bin ein Koch-Bot. Nenne die Zutaten und ich sage dir, was du kochen kannst.",
        "start_manual": "?? **Sende eine Sprachnachricht oder Text** mit Zutaten.\n?? Oder schreibe **\"Rezept fur [Gericht]\"**.",
        "processing": "????? Denke nach...",
        "menu": "?? **Was kochen wir?**",
        "choose_language": "?? **Sprache wahlen:**",
        
        "soup": "?? Suppen",
        "main": "?? Hauptgerichte",
        "salad": "?? Salate",
        "breakfast": "?? Fruhstuck",
        "dessert": "?? Desserts",
        "drink": "?? Getranke",
        "snack": "?? Snacks",
        
        "btn_favorites": "? Favoriten",
        "btn_restart": "?? Neustart",
        "btn_change_lang": "?? Sprache andern",
        "btn_help": "????? Hilfe",
        "btn_add_to_fav": "? Zu Favoriten",
        "btn_remove_from_fav": "? In Favoriten",
        "btn_back": "?? Zuruck",
        "btn_next": "Weiter ??",
        "btn_prev": "?? Zuruck",
        "btn_hide": "?? Ausblenden",
        "btn_another": "?? Andere Variante",
        "btn_to_categories": "?? Zu Kategorien",
        
        "favorites_empty": "? Sie haben noch keine Favoriten.",
        "favorites_list": "? **Favoriten** (Seite {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. **{dish}**\n   ?? {date}\n",
        "recipe_added_to_fav": "? Rezept zu Favoriten hinzugefugt!",
        "recipe_removed_from_fav": "??? Rezept aus Favoriten entfernt.",
        
        "error_voice": "?? Sprache nicht erkannt. Bitte versuchen Sie es erneut.",
        "error_generation": "? Generierungsfehler. Bitte versuchen Sie es erneut.",
        "error_no_products": "?? Ich sehe keine Produkte. Versuchen Sie: 'Karotten, Zwiebeln, Kartoffeln'.",
        "error_too_long": "?? Nachricht zu lang. Maximum 1000 Zeichen.",
        
        "products_accepted": "? Produkte akzeptiert: {products}",
        "products_added": "? Hinzugefugt: {products}",
        "choose_category": "?? **Kategorie wahlen:**",
        "choose_dish": "?? **Gericht wahlen:**",
        
        "lang_changed": "?? Sprache auf Deutsch geandert.",
        "lang_ru": "???? Русский",
        "lang_en": "???? English",
        "lang_de": "???? Deutsch",
        "lang_fr": "???? Francais",
        "lang_it": "???? Italiano",
        "lang_es": "???? Espanol",
        
        "help_title": "????? **Koch-Bot Hilfe**",
        "help_text": """
*So funktioniert's:*
1. Zutaten senden (Text oder Sprache)
2. Gerichtkategorie wahlen
3. Gericht aus Liste wahlen
4. Rezept erhalten

*Befehle:*
/start - neu starten
/favorites - Lieblingsrezepte
/lang - Sprache andern
/help - Hilfe

*Tipps:*
- Sie konnen mehrmals Zutaten hinzufugen
- Klicken Sie ? unter Rezept zum Speichern
- Sprachnachrichten werden automatisch geloscht

*Support:* @support
        """,
        
        "thanks": "Gern geschehen! ?????",
        "easter_egg": "?? Sie haben ein Osterei gefunden!",
    },
    
    "fr": {
        "welcome": "?? Bonjour, {name} !\n\nJe suis un bot chef. Nommez les ingredients et je vous dirai quoi cuisiner.",
        "start_manual": "?? **Envoyez un message vocal ou texte** avec les ingredients.\n?? Ou ecrivez **\"Recette de [plat]\"**.",
        "processing": "????? Je reflechis...",
        "menu": "?? **Que cuisinons-nous ?**",
        "choose_language": "?? **Choisir la langue :**",
        
        "soup": "?? Soupes",
        "main": "?? Plats principaux",
        "salad": "?? Salades",
        "breakfast": "?? Petit-dejeuner",
        "dessert": "?? Desserts",
        "drink": "?? Boissons",
        "snack": "?? Snacks",
        
        "btn_favorites": "? Favoris",
        "btn_restart": "?? Redemarrer",
        "btn_change_lang": "?? Changer de langue",
        "btn_help": "????? Aide",
        "btn_add_to_fav": "? Ajouter aux favoris",
        "btn_remove_from_fav": "? Dans les favoris",
        "btn_back": "?? Retour",
        "btn_next": "Suivant ??",
        "btn_prev": "?? Precedent",
        "btn_hide": "?? Cacher",
        "btn_another": "?? Autre variante",
        "btn_to_categories": "?? Aux categories",
        
        "favorites_empty": "? Vous n'avez pas encore de recettes favorites.",
        "favorites_list": "? **Favoris** (page {page}/{total_pages}) :\n\n{recipes}",
        "favorites_recipe_item": "{num}. **{dish}**\n   ?? {date}\n",
        "recipe_added_to_fav": "? Recette ajoutee aux favoris !",
        "recipe_removed_from_fav": "??? Recette retiree des favoris.",
        
        "error_voice": "?? Impossible de reconnaitre la voix. Veuillez reessayer.",
        "error_generation": "? Erreur de generation. Veuillez reessayer.",
        "error_no_products": "?? Je ne vois pas de produits. Essayez : 'carottes, oignons, pommes de terre'.",
        "error_too_long": "?? Message trop long. Maximum 1000 caracteres.",
        
        "products_accepted": "? Produits acceptes : {products}",
        "products_added": "? Ajoute : {products}",
        "choose_category": "?? **Choisir une categorie :**",
        "choose_dish": "?? **Choisir un plat :**",
        
        "lang_changed": "?? Langue changee en francais.",
        "lang_ru": "???? Русский",
        "lang_en": "???? English",
        "lang_de": "???? Deutsch",
        "lang_fr": "???? Francais",
        "lang_it": "???? Italiano",
        "lang_es": "???? Espanol",
        
        "help_title": "????? **Aide du Bot Chef**",
        "help_text": """
*Comment utiliser :*
1. Envoyer les ingredients (texte ou voix)
2. Choisir une categorie de plat
3. Choisir un plat dans la liste
4. Obtenir la recette

*Commandes :*
/start - recommencer
/favorites - recettes favorites
/lang - changer de langue
/help - aide

*Conseils :*
- Vous pouvez ajouter des ingredients plusieurs fois
- Cliquez ? sous la recette pour sauvegarder
- Les messages vocaux sont automatiquement supprimes

*Support :* @support
        """,
        
        "thanks": "De rien ! ?????",
        "easter_egg": "?? Vous avez trouve un ?uf de Paques !",
    },
    
    "it": {
        "welcome": "?? Ciao, {name}!\n\nSono un bot chef. Nomina gli ingredienti e ti diro cosa cucinare.",
        "start_manual": "?? **Invia un messaggio vocale o testo** con gli ingredienti.\n?? O scrivi **\"Ricetta per [piatto]\"**.",
        "processing": "????? Sto pensando...",
        "menu": "?? **Cosa cuciniamo?**",
        "choose_language": "?? **Scegli la lingua:**",
        
        "soup": "?? Zuppe",
        "main": "?? Piatti principali",
        "salad": "?? Insalate",
        "breakfast": "?? Colazione",
        "dessert": "?? Dolci",
        "drink": "?? Bevande",
        "snack": "?? Snack",
        
        "btn_favorites": "? Preferiti",
        "btn_restart": "?? Riavvia",
        "btn_change_lang": "?? Cambia lingua",
        "btn_help": "????? Aiuto",
        "btn_add_to_fav": "? Aggiungi ai preferiti",
        "btn_remove_from_fav": "? Nei preferiti",
        "btn_back": "?? Indietro",
        "btn_next": "Avanti ??",
        "btn_prev": "?? Indietro",
        "btn_hide": "?? Nascondi",
        "btn_another": "?? Altra variante",
        "btn_to_categories": "?? Alle categorie",
        
        "favorites_empty": "? Non hai ancora ricette preferite.",
        "favorites_list": "? **Preferiti** (pagina {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. **{dish}**\n   ?? {date}\n",
        "recipe_added_to_fav": "? Ricetta aggiunta ai preferiti!",
        "recipe_removed_from_fav": "??? Ricetta rimossa dai preferiti.",
        
        "error_voice": "?? Impossibile riconoscere la voce. Per favore riprova.",
        "error_generation": "? Errore di generazione. Per favore riprova.",
        "error_no_products": "?? Non vedo prodotti. Prova: 'carote, cipolle, patate'.",
        "error_too_long": "?? Messaggio troppo lungo. Massimo 1000 caratteri.",
        
        "products_accepted": "? Prodotti accettati: {products}",
        "products_added": "? Aggiunto: {products}",
        "choose_category": "?? **Scegli una categoria:**",
        "choose_dish": "?? **Scegli un piatto:**",
        
        "lang_changed": "?? Lingua cambiata in italiano.",
        "lang_ru": "???? Русский",
        "lang_en": "???? English",
        "lang_de": "???? Deutsch",
        "lang_fr": "???? Francais",
        "lang_it": "???? Italiano",
        "lang_es": "???? Espanol",
        
        "help_title": "????? **Aiuto Bot Chef**",
        "help_text": """
*Come usare:*
1. Invia ingredienti (testo o voce)
2. Scegli categoria piatto
3. Scegli piatto dalla lista
4. Ottieni ricetta

*Comandi:*
/start - ricomincia
/favorites - ricette preferite
/lang - cambia lingua
/help - aiuto

*Suggerimenti:*
- Puoi aggiungere ingredienti piu volte
- Clicca ? sotto la ricetta per salvare
- I messaggi vocali vengono automaticamente eliminati

*Supporto:* @support
        """,
        
        "thanks": "Prego! ?????",
        "easter_egg": "?? Hai trovato un uovo di Pasqua!",
    },
    
    "es": {
        "welcome": "?? ?Hola, {name}!\n\nSoy un bot chef. Nombra los ingredientes y te dire que cocinar.",
        "start_manual": "?? **Envia un mensaje de voz o texto** con ingredientes.\n?? O escribe **\"Receta de [plato]\"**.",
        "processing": "????? Pensando...",
        "menu": "?? **?Que cocinamos?**",
        "choose_language": "?? **Elegir idioma:**",
        
        "soup": "?? Sopas",
        "main": "?? Platos principales",
        "salad": "?? Ensaladas",
        "breakfast": "?? Desayuno",
        "dessert": "?? Postres",
        "drink": "?? Bebidas",
        "snack": "?? Bocadillos",
        
        "btn_favorites": "? Favoritos",
        "btn_restart": "?? Reiniciar",
        "btn_change_lang": "?? Cambiar idioma",
        "btn_help": "????? Ayuda",
        "btn_add_to_fav": "? Anadir a favoritos",
        "btn_remove_from_fav": "? En favoritos",
        "btn_back": "?? Atras",
        "btn_next": "Siguiente ??",
        "btn_prev": "?? Atras",
        "btn_hide": "?? Ocultar",
        "btn_another": "?? Otra variante",
        "btn_to_categories": "?? A categorias",
        
        "favorites_empty": "? Aun no tienes recetas favoritas.",
        "favorites_list": "? **Favoritos** (pagina {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. **{dish}**\n   ?? {date}\n",
        "recipe_added_to_fav": "? ?Receta anadida a favoritos!",
        "recipe_removed_from_fav": "??? Receta eliminada de favoritos.",
        
        "error_voice": "?? No se pudo reconocer la voz. Por favor, intentalo de nuevo.",
        "error_generation": "? Error de generacion. Por favor, intentalo de nuevo.",
        "error_no_products": "?? No veo productos. Prueba: 'zanahorias, cebollas, patatas'.",
        "error_too_long": "?? Mensaje demasiado largo. Maximo 1000 caracteres.",
        
        "products_accepted": "? Productos aceptados: {products}",
        "products_added": "? Anadido: {products}",
        "choose_category": "?? **Elegir categoria:**",
        "choose_dish": "?? **Elegir un plato:**",
        
        "lang_changed": "?? Idioma cambiado a espanol.",
        "lang_ru": "???? Русский",
        "lang_en": "???? English",
        "lang_de": "???? Deutsch",
        "lang_fr": "???? Francais",
        "lang_it": "???? Italiano",
        "lang_es": "???? Espanol",
        
        "help_title": "????? **Ayuda del Bot Chef**",
        "help_text": """
*Como usar:*
1. Enviar ingredientes (texto o voz)
2. Elegir categoria de plato
3. Elegir plato de la lista
4. Obtener receta

*Comandos:*
/start - empezar de nuevo
/favorites - recetas favoritas
/lang - cambiar idioma
/help - ayuda

*Consejos:*
- Puedes anadir ingredientes varias veces
- Haz clic en ? bajo la receta para guardar
- Los mensajes de voz se eliminan automaticamente

*Soporte:* @support
        """,
        
        "thanks": "?De nada! ?????",
        "easter_egg": "?? ?Encontraste un huevo de Pascua!",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    """Получает текст на нужном языке с подстановкой переменных"""
    # Если язык не поддерживается, используем русский
    if lang not in TEXTS:
        lang = "ru"
    
    lang_dict = TEXTS.get(lang, TEXTS["ru"])
    text = lang_dict.get(key, TEXTS["ru"].get(key, key))
    
    # Подставляем переменные, если они есть
    if kwargs and text:
        try:
            return text.format(**kwargs)
        except KeyError:
            # Если ошибка подстановки, возвращаем текст без форматирования
            return text
    
    return text