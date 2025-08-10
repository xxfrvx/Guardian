from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def consent_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Продолжить ✅", callback_data="accept_terms")],
        [InlineKeyboardButton("Условия использования", callback_data="show_terms"),
         InlineKeyboardButton("Политика", callback_data="show_privacy")]
    ])

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 Проверить пользователя", callback_data="menu:check")],
        [InlineKeyboardButton("⚠️ Пожаловаться", callback_data="menu:report"),
         InlineKeyboardButton("👍 Похвалить", callback_data="menu:praise")],
        [InlineKeyboardButton("🪙 Проверить монету", callback_data="menu:coin_check"),
         InlineKeyboardButton("🚩 Сообщить монету", callback_data="menu:coin_report")],
        [InlineKeyboardButton("🛡 Модерация", callback_data="menu:moderation"),
         InlineKeyboardButton("👤 Мой профиль", callback_data="menu:profile")]
    ])

def report_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Мошенничество", callback_data="report:fraud"),
         InlineKeyboardButton("Фишинг/линк", callback_data="report:phishing")],
        [InlineKeyboardButton("Спам/реклама", callback_data="report:spam")],
        [InlineKeyboardButton("Отмена", callback_data="cancel")]
    ])

def moderation_case_kb(case_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"mod:approve:{case_id}"),
         InlineKeyboardButton("❌ Отклонить", callback_data=f"mod:reject:{case_id}")],
        [InlineKeyboardButton("↩️ Позже", callback_data="mod:later")]
    ])

def praise_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Быстро похвалить 👍", callback_data="praise:quick")],
        [InlineKeyboardButton("Отмена", callback_data="cancel")]
    ])

def coin_case_kb(coin_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ В список скамов", callback_data=f"coin:approve:{coin_id}"),
         InlineKeyboardButton("❌ Отклонить", callback_data=f"coin:reject:{coin_id}")],
        [InlineKeyboardButton("↩️ Позже", callback_data="coin:later")]
    ])
