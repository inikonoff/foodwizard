from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

TEXTS: Dict[str, Dict[str, str]] = {
    # ================= РУССКИЙ (RU) =================
    "ru": {
        # --- ВИТРИНА БОТА ---
        "bot_description": """🧙‍♂️ **Food Wizard — ваш личный ИИ-шеф!**

Не знаете, что приготовить из того, что есть в холодильнике? Продукты пропадают, а идей нет?

Просто скажите мне, что у вас есть, и я сотворю кулинарную магию! ✨

**Я умею:**
🥦 Подбирать рецепты из любых ингредиентов
🎙 Понимать голосовые сообщения (просто диктуйте!)
🌍 Говорить на 6 языках
⭐️ Сохранять ваши любимые рецепты

**Давайте что-нибудь приготовим!** 👇""",

        "bot_short_description": "🥘 Умный кулинарный ИИ. Перечислите продукты, а я дам рецепт чего-нибудь вкусненького из них.",

        # --- ЧАТ ---
        "welcome": """👋 Здравствуйте.

🎤 Отправьте голосовое или текстовое сообщение с перечнем продуктов, и я подскажу, что из них можно приготовить.

📝 Или напишите "Дай рецепт [блюдо]".""",
        
        "start_manual": "", 
        "processing": "⏳ Думаю...",
        "menu": "🍴 **Что будем готовить?**",
        "choose_language": "🌐 **Выберите язык:**",
        
        # Категории
        "soup": "🍜 Супы",
        "main": "🥩 Вторые блюда",
        "salad": "🥗 Салаты",
        "breakfast": "🥞 Завтраки",
        "dessert": "🍰 Десерты",
        "drink": "🍹 Напитки",
        "snack": "🥨 Закуски",
        
        # Кнопки
        "btn_favorites": "⭐️ Избранное",
        "btn_restart": "🔄 Рестарт",
        "btn_change_lang": "🌐 Сменить язык",
        "btn_help": "❓ Помощь",
        "btn_add_to_fav": "☆ В избранное",
        "btn_remove_from_fav": "🌟 В избранном",
        "btn_back": "⬅️ Назад",
        "btn_another": "➡️ Ещё рецепт",
        "btn_buy_premium": "💎 Премиум",
        "btn_page": "Стр. {page}/{total}",
        
        # Рецепты и сообщения
        "choose_category": "📝 **Выберите категорию блюд:**",
        "choose_dish": "🍳 **Выберите блюдо:**",
        "recipe_title": "✨ **Рецепт: {dish_name}**",
        "recipe_ingredients": "🛒 **Ингредиенты:**",
        "recipe_instructions": "📝 **Инструкция:**",
        "recipe_error": "❌ Не удалось сгенерировать рецепт. Попробуйте снова или выберите другое блюдо.",
        "dish_list_error": "❌ Не удалось получить список блюд. Попробуйте снова или измените продукты.",
        "error_session_expired": "Время сессии истекло. Пожалуйста, начните заново, отправив список продуктов.",
        
        # Избранное
        "favorites_title": "⭐️ **Ваши избранные рецепты**",
        "favorites_empty": "😔 Список избранного пуст.",
        "favorite_added": "⭐ Рецепт **{dish_name}** добавлен в избранное!",
        "favorite_removed": "🗑 Рецепт **{dish_name}** удален из избранного.",
        "favorite_limit": "❌ Достигнут лимит избранных рецептов ({limit}).",
        "favorites_list": "⭐️ **Ваши избранные рецепты** (стр. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (от {date})\n",
        
        # Ошибки
        "limit_voice_exceeded": "❌ **Лимит голосовых запросов исчерпан!**\n\nВы использовали {used} из {limit} голосовых запросов сегодня. Лимиты обновляются каждый день в 00:00.\n\n💎 **Хотите больше?** Используйте команду /stats",
        "limit_text_exceeded": "❌ **Лимит текстовых запросов исчерпан!**\n\nВы использовали {used} из {limit} текстовых запросов сегодня. Лимиты обновляются каждый день в 00:00.\n\n💎 **Хотите больше?** Используйте команду /stats",
        "error_voice_recognition": "🗣️ **Ошибка распознавания голоса.** Пожалуйста, попробуйте говорить четче или используйте текстовый ввод.",
        "error_generation": "❌ Произошла ошибка. Попробуйте ещё раз.",
        "error_unknown": "❌ Произошла неизвестная ошибка.",
        "error_not_enough_products": "🤔 Не могу понять, что приготовить. Пожалуйста, назовите больше продуктов.",
        "voice_recognized": "✅ Распознано: {text}",
        "lang_changed": "🌐 Язык успешно изменен на русский.",
        "safety_refusal": "🚫 Извините, я готовлю только еду. Могу предложить рецепты блюд из разных кухонь мира! 🌍",
        
        "help_title": "❓ **Помощь**",
        "help_text": "Просто отправьте список продуктов, и я подберу рецепт.",
    },
    
    # ================= АНГЛИЙСКИЙ (EN) =================
    "en": {
        "bot_description": """🧙‍♂️ **Food Wizard — Your Personal AI Chef!**

Don't know what to cook with what's in your fridge? Ingredients going to waste with no ideas?

Just tell me what you have, and I'll work my culinary magic! ✨

**I can:**
🥦 Match recipes to any ingredients
🎙 Understand voice messages (just speak!)
🌍 Speak 6 languages
⭐️ Save your favorite recipes

**Let's cook something!** 👇""",

        "bot_short_description": "🥘 Smart Culinary AI. List your ingredients, and I'll give you a tasty recipe. More ingredients — more variety!",

        "welcome": """👋 Hello.

🎤 Send a voice or text message listing your ingredients, and I'll suggest what you can cook with them.

📝 Or write "Give me a recipe for [dish]".""",
        
        "start_manual": "", 
        "processing": "⏳ Thinking...",
        "menu": "🍴 **What should we cook?**",
        "choose_language": "🌐 **Choose Language:**",
        "soup": "🍜 Soups",
        "main": "🥩 Main Courses",
        "salad": "🥗 Salads",
        "breakfast": "🥞 Breakfasts",
        "dessert": "🍰 Desserts",
        "drink": "🍹 Drinks",
        "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favorites",
        "btn_restart": "🔄 Restart",
        "btn_change_lang": "🌐 Change Language",
        "btn_help": "❓ Help",
        "btn_add_to_fav": "☆ Add to Favorites",
        "btn_remove_from_fav": "🌟 In Favorites",
        "btn_back": "⬅️ Back",
        "btn_another": "➡️ Another Recipe",
        "btn_buy_premium": "💎 Premium",
        "btn_page": "Page {page}/{total}",
        
        "choose_category": "📝 **Select a dish category:**",
        "choose_dish": "🍳 **Select a dish:**",
        "recipe_title": "✨ **Recipe: {dish_name}**",
        "recipe_ingredients": "🛒 **Ingredients:**",
        "recipe_instructions": "📝 **Instructions:**",
        "recipe_error": "❌ Could not generate a recipe. Please try again or select another dish.",
        "dish_list_error": "❌ Could not get a list of dishes. Please try again or change your ingredients.",
        "error_session_expired": "Session time expired. Please start over by sending a list of ingredients.",
        
        "favorites_title": "⭐️ **Your Favorite Recipes**",
        "favorites_empty": "😔 Your favorites list is empty.",
        "favorite_added": "⭐ Recipe **{dish_name}** added to favorites!",
        "favorite_removed": "🗑 Recipe **{dish_name}** removed from favorites.",
        "favorite_limit": "❌ Favorite recipes limit reached ({limit}).",
        "favorites_list": "⭐️ **Your Favorite Recipes** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (from {date})\n",
        
        "limit_voice_exceeded": "❌ **Voice Request Limit Exceeded!**\n\nYou have used {used} of {limit} voice requests today. Limits refresh daily at 00:00.\n\n💎 **Want more?** Use the /stats command",
        "limit_text_exceeded": "❌ **Text Request Limit Exceeded!**\n\nYou have used {used} of {limit} text requests today. Limits refresh daily at 00:00.\n\n💎 **Want more?** Use the /stats command",
        "error_voice_recognition": "🗣️ **Voice recognition error.** Please try speaking clearer or use text input.",
        "error_generation": "❌ An error occurred. Please try again.",
        "error_unknown": "❌ An unknown error occurred.",
        "error_not_enough_products": "🤔 I can't figure out what to cook. Please name more ingredients.",
        "voice_recognized": "✅ Recognized: {text}",
        "lang_changed": "🌐 Language successfully changed to English.",
        "safety_refusal": "🚫 Sorry, I only cook food. I can offer recipes from different world cuisines! 🌍",
        "help_title": "❓ **Bot Chef Help**",
        "help_text": "Just send a list of ingredients, and I'll pick a recipe.",
    },

    # ================= НЕМЕЦКИЙ (DE) =================
    "de": {
        "bot_description": """🧙‍♂️ **Food Wizard — Ihr persönlicher KI-Koch!**

Wissen Sie nicht, was Sie aus dem Inhalt Ihres Kühlschranks kochen sollen? Lebensmittel verderben?

Sagen Sie mir einfach, was Sie haben, und ich vollbringe kulinarische Magie! ✨

**Ich kann:**
🥦 Rezepte für beliebige Zutaten finden
🎙 Sprachnachrichten verstehen
🌍 6 Sprachen sprechen
⭐️ Ihre Lieblingsrezepte speichern

**Lassen Sie uns etwas kochen!** 👇""",

        "bot_short_description": "🥘 Smarte Kulinarik-KI. Nennen Sie Zutaten, und ich gebe Ihnen ein leckeres Rezept.",

        "welcome": """👋 Hallo.

🎤 Senden Sie eine Sprach- oder Textnachricht mit einer Liste Ihrer Zutaten, und ich schlage vor, was Sie daraus kochen können.

📝 Oder schreiben Sie "Gib mir ein Rezept für [Gericht]".""",

        "start_manual": "",
        "processing": "⏳ Ich denke nach...",
        "menu": "🍴 **Was kochen wir?**",
        "choose_language": "🌐 **Sprache wählen:**",
        "soup": "🍜 Suppen",
        "main": "🥩 Hauptgerichte",
        "salad": "🥗 Salate",
        "breakfast": "🥞 Frühstücke",
        "dessert": "🍰 Desserts",
        "drink": "🍹 Getränke",
        "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoriten",
        "btn_restart": "🔄 Neustart",
        "btn_change_lang": "🌐 Sprache ändern",
        "btn_help": "❓ Hilfe",
        "btn_add_to_fav": "☆ Zu Favoriten",
        "btn_remove_from_fav": "🌟 Gespeichert",
        "btn_back": "⬅️ Zurück",
        "btn_another": "➡️ Anderes Rezept",
        "btn_buy_premium": "💎 Premium",
        "btn_page": "Seite {page}/{total}",
        
        "choose_category": "📝 **Wählen Sie eine Kategorie:**",
        "choose_dish": "🍳 **Wählen Sie ein Gericht:**",
        "recipe_title": "✨ **Rezept: {dish_name}**",
        "recipe_ingredients": "🛒 **Zutaten:**",
        "recipe_instructions": "📝 **Anleitung:**",
        "recipe_error": "❌ Rezept konnte nicht erstellt werden.",
        "dish_list_error": "❌ Gerichteliste konnte nicht geladen werden.",
        "error_session_expired": "Sitzung abgelaufen. Bitte starten Sie neu.",
        
        "favorites_title": "⭐️ **Ihre Favoriten**",
        "favorites_empty": "😔 Favoritenliste ist leer.",
        "favorite_added": "⭐ Rezept **{dish_name}** gespeichert!",
        "favorite_removed": "🗑 Rezept **{dish_name}** gelöscht.",
        "favorite_limit": "❌ Limit für Favoriten erreicht ({limit}).",
        "favorites_list": "⭐️ **Favoriten** (Seite {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (vom {date})\n",
        
        "limit_voice_exceeded": "❌ **Sprachlimit erreicht!**\n\nNutzen Sie /stats für mehr.",
        "limit_text_exceeded": "❌ **Textlimit erreicht!**\n\nNutzen Sie /stats für mehr.",
        "error_voice_recognition": "🗣️ **Fehler bei Spracherkennung.** Bitte deutlicher sprechen.",
        "error_generation": "❌ Fehler aufgetreten.",
        "error_unknown": "❌ Unbekannter Fehler.",
        "error_not_enough_products": "🤔 Ich weiß nicht, was ich kochen soll. Mehr Zutaten bitte.",
        "voice_recognized": "✅ Erkannt: {text}",
        "lang_changed": "🌐 Sprache auf Deutsch geändert.",
        "safety_refusal": "🚫 Ich koche nur Essen. Aber ich kenne Rezepte aus aller Welt! 🌍",
        "help_title": "❓ **Hilfe**",
        "help_text": "Senden Sie einfach eine Zutatenliste.",
    },

    # ================= ФРАНЦУЗСКИЙ (FR) =================
    "fr": {
        "bot_description": """🧙‍♂️ **Food Wizard — Votre Chef IA Personnel !**

Vous ne savez pas quoi cuisiner avec ce qu'il y a dans votre frigo ?

Dites-moi simplement ce que vous avez, et je ferai de la magie culinaire ! ✨

**Je peux :**
🥦 Trouver des recettes pour tous les ingrédients
🎙 Comprendre les messages vocaux
🌍 Parler 6 langues
⭐️ Sauvegarder vos favoris

**Cuisinons quelque chose !** 👇""",

        "bot_short_description": "🥘 IA Culinaire Intelligente. Listez vos ingrédients, et je vous donnerai une recette savoureuse.",

        "welcome": """👋 Bonjour.

🎤 Envoyez un message vocal ou texte avec la liste de vos ingrédients, et je vous suggérerai quoi cuisiner.

📝 Ou écrivez "Donne-moi une recette de [plat]".""",

        "start_manual": "",
        "processing": "⏳ Je réfléchis...",
        "menu": "🍴 **Que cuisinons-nous ?**",
        "choose_language": "🌐 **Choisir la langue :**",
        "soup": "🍜 Soupes",
        "main": "🥩 Plats principaux",
        "salad": "🥗 Salades",
        "breakfast": "🥞 Petit-déjeuner",
        "dessert": "🍰 Desserts",
        "drink": "🍹 Boissons",
        "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoris",
        "btn_restart": "🔄 Redémarrer",
        "btn_change_lang": "🌐 Langue",
        "btn_help": "❓ Aide",
        "btn_add_to_fav": "☆ Aux Favoris",
        "btn_remove_from_fav": "🌟 Enregistré",
        "btn_back": "⬅️ Retour",
        "btn_another": "➡️ Autre recette",
        "btn_buy_premium": "💎 Premium",
        "btn_page": "Page {page}/{total}",
        
        "choose_category": "📝 **Choisissez une catégorie :**",
        "choose_dish": "🍳 **Choisissez un plat :**",
        "recipe_title": "✨ **Recette : {dish_name}**",
        "recipe_ingredients": "🛒 **Ingrédients :**",
        "recipe_instructions": "📝 **Instructions :**",
        "recipe_error": "❌ Impossible de générer la recette.",
        "dish_list_error": "❌ Impossible d'obtenir la liste.",
        "error_session_expired": "Session expirée. Recommencez SVP.",
        
        "favorites_title": "⭐️ **Vos Favoris**",
        "favorites_empty": "😔 Liste vide.",
        "favorite_added": "⭐ Recette **{dish_name}** ajoutée !",
        "favorite_removed": "🗑 Recette **{dish_name}** supprimée.",
        "favorite_limit": "❌ Limite de favoris atteinte ({limit}).",
        "favorites_list": "⭐️ **Favoris** (page {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (du {date})\n",
        
        "limit_voice_exceeded": "❌ **Limite vocale atteinte !**\n\nUtilisez /stats pour plus.",
        "limit_text_exceeded": "❌ **Limite textuelle atteinte !**\n\nUtilisez /stats pour plus.",
        "error_voice_recognition": "🗣️ **Erreur vocale.** Parlez plus clairement SVP.",
        "error_generation": "❌ Erreur survenue.",
        "error_unknown": "❌ Erreur inconnue.",
        "error_not_enough_products": "🤔 Je ne sais pas quoi cuisiner. Plus d'ingrédients SVP.",
        "voice_recognized": "✅ Reconnu : {text}",
        "lang_changed": "🌐 Langue changée en Français.",
        "safety_refusal": "🚫 Je ne cuisine que de la nourriture. 🌍",
        "help_title": "❓ **Aide**",
        "help_text": "Envoyez simplement une liste d'ingrédients.",
    },

    # ================= ИТАЛЬЯНСКИЙ (IT) =================
    "it": {
        "bot_description": """🧙‍♂️ **Food Wizard — Il tuo Chef IA Personale!**

Non sai cosa cucinare con quello che c'è in frigo?

Dimmi cosa hai e farò una magia culinaria! ✨

**Posso:**
🥦 Trovare ricette per qualsiasi ingrediente
🎙 Capire i messaggi vocali
🌍 Parlare 6 lingue
⭐️ Salvare i tuoi preferiti

**Cuciniamo qualcosa!** 👇""",

        "bot_short_description": "🥘 IA Culinaria Intelligente. Elenca gli ingredienti e ti darò una ricetta gustosa.",

        "welcome": """👋 Ciao.

🎤 Invia un messaggio vocale o di testo con l'elenco dei tuoi ingredienti e ti suggerirò cosa cucinare.

📝 O scrivi "Dammi una ricetta per [piatto]".""",

        "start_manual": "",
        "processing": "⏳ Sto pensando...",
        "menu": "🍴 **Cosa cuciniamo?**",
        "choose_language": "🌐 **Scegli lingua:**",
        "soup": "🍜 Zuppe",
        "main": "🥩 Secondi",
        "salad": "🥗 Insalate",
        "breakfast": "🥞 Colazione",
        "dessert": "🍰 Dessert",
        "drink": "🍹 Bevande",
        "snack": "🥨 Snack",
        
        "btn_favorites": "⭐️ Preferiti",
        "btn_restart": "🔄 Riavvia",
        "btn_change_lang": "🌐 Lingua",
        "btn_help": "❓ Aiuto",
        "btn_add_to_fav": "☆ Nei Preferiti",
        "btn_remove_from_fav": "🌟 Salvato",
        "btn_back": "⬅️ Indietro",
        "btn_another": "➡️ Altra ricetta",
        "btn_buy_premium": "💎 Premium",
        "btn_page": "Pag. {page}/{total}",
        
        "choose_category": "📝 **Scegli categoria:**",
        "choose_dish": "🍳 **Scegli piatto:**",
        "recipe_title": "✨ **Ricetta: {dish_name}**",
        "recipe_ingredients": "🛒 **Ingredienti:**",
        "recipe_instructions": "📝 **Istruzioni:**",
        "recipe_error": "❌ Impossibile generare la ricetta.",
        "dish_list_error": "❌ Errore lista piatti.",
        "error_session_expired": "Sessione scaduta. Ricomincia.",
        
        "favorites_title": "⭐️ **I tuoi Preferiti**",
        "favorites_empty": "😔 Lista vuota.",
        "favorite_added": "⭐ Ricetta **{dish_name}** salvata!",
        "favorite_removed": "🗑 Ricetta **{dish_name}** rimossa.",
        "favorite_limit": "❌ Limite preferiti raggiunto ({limit}).",
        "favorites_list": "⭐️ **Preferiti** (pag. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (del {date})\n",
        
        "limit_voice_exceeded": "❌ **Limite vocale superato!**\n\nUsa /stats.",
        "limit_text_exceeded": "❌ **Limite testo superato!**\n\nUsa /stats.",
        "error_voice_recognition": "🗣️ **Errore vocale.** Parla più chiaramente.",
        "error_generation": "❌ Errore.",
        "error_unknown": "❌ Errore sconosciuto.",
        "error_not_enough_products": "🤔 Non so cosa cucinare. Più ingredienti per favore.",
        "voice_recognized": "✅ Riconosciuto: {text}",
        "lang_changed": "🌐 Lingua cambiata in Italiano.",
        "safety_refusal": "🚫 Cucino solo cibo. 🌍",
        "help_title": "❓ **Aiuto**",
        "help_text": "Invia solo una lista di ingredienti.",
    },

    # ================= ИСПАНСКИЙ (ES) =================
    "es": {
        "bot_description": """🧙‍♂️ **Food Wizard — ¡Tu Chef Personal de IA!**

¿No sabes qué cocinar con lo que hay en el refri?

¡Dime qué tienes y haré magia culinaria! ✨

**Puedo:**
🥦 Encontrar recetas para cualquier ingrediente
🎙 Entender mensajes de voz
🌍 Hablar 6 idiomas
⭐️ Guardar tus favoritos

**¡Cocinemos algo!** 👇""",

        "bot_short_description": "🥘 IA Culinaria Inteligente. Enumera tus ingredientes y te daré una receta sabrosa.",

        "welcome": """👋 Hola.

🎤 Envía un mensaje de voz o texto con la lista de tus ingredientes y te sugeriré qué cocinar.

📝 O escribe "Dame una receta de [plato]".""",

        "start_manual": "",
        "processing": "⏳ Pensando...",
        "menu": "🍴 **¿Qué cocinamos?**",
        "choose_language": "🌐 **Idioma:**",
        "soup": "🍜 Sopas",
        "main": "🥩 Platos principales",
        "salad": "🥗 Ensaladas",
        "breakfast": "🥞 Desayunos",
        "dessert": "🍰 Postres",
        "drink": "🍹 Bebidas",
        "snack": "🥨 Snacks",
        
        "btn_favorites": "⭐️ Favoritos",
        "btn_restart": "🔄 Reiniciar",
        "btn_change_lang": "🌐 Idioma",
        "btn_help": "❓ Ayuda",
        "btn_add_to_fav": "☆ A Favoritos",
        "btn_remove_from_fav": "🌟 Guardado",
        "btn_back": "⬅️ Atrás",
        "btn_another": "➡️ Otra receta",
        "btn_buy_premium": "💎 Premium",
        "btn_page": "Pág. {page}/{total}",
        
        "choose_category": "📝 **Elige categoría:**",
        "choose_dish": "🍳 **Elige plato:**",
        "recipe_title": "✨ **Receta: {dish_name}**",
        "recipe_ingredients": "🛒 **Ingredientes:**",
        "recipe_instructions": "📝 **Instrucciones:**",
        "recipe_error": "❌ No se pudo generar la receta.",
        "dish_list_error": "❌ Error al obtener la lista.",
        "error_session_expired": "Sesión expirada. Empieza de nuevo.",
        
        "favorites_title": "⭐️ **Tus Favoritos**",
        "favorites_empty": "😔 Lista vacía.",
        "favorite_added": "⭐ ¡Receta **{dish_name}** guardada!",
        "favorite_removed": "🗑 Receta **{dish_name}** eliminada.",
        "favorite_limit": "❌ Límite de favoritos alcanzado ({limit}).",
        "favorites_list": "⭐️ **Favoritos** (pág. {page}/{total_pages}):\n\n{recipes}",
        "favorites_recipe_item": "{num}. {dish} (del {date})\n",
        
        "limit_voice_exceeded": "❌ **¡Límite de voz superado!**\n\nUsa /stats.",
        "limit_text_exceeded": "❌ **¡Límite de texto superado!**\n\nUsa /stats.",
        "error_voice_recognition": "🗣️ **Error de voz.** Habla más claro.",
        "error_generation": "❌ Error.",
        "error_unknown": "❌ Error desconocido.",
        "error_not_enough_products": "🤔 No sé qué cocinar. Más ingredientes por favor.",
        "voice_recognized": "✅ Reconocido: {text}",
        "lang_changed": "🌐 Idioma cambiado a Español.",
        "safety_refusal": "🚫 Solo cocino comida. 🌍",
        "help_title": "❓ **Ayuda**",
        "help_text": "Solo envía una lista de ingredientes.",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    if lang not in TEXTS: lang = "ru"
    lang_dict = TEXTS.get(lang, TEXTS["ru"])
    text = lang_dict.get(key, TEXTS["ru"].get(key, ""))
    if kwargs and text:
        try: return text.format(**kwargs)
        except KeyError: 
            logger.warning(f"Key error in text: {key}")
            return text
    return text
    