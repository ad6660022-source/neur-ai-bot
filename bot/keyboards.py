from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


# ─────────────────────────────────────────────
#  Main Menu
# ─────────────────────────────────────────────
def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 ChatGPT", callback_data="ai:chatgpt"),
            InlineKeyboardButton(text="🟣 Claude",  callback_data="ai:claude"),
        ],
        [
            InlineKeyboardButton(text="🔵 DeepSeek", callback_data="ai:deepseek"),
        ],
        [
            InlineKeyboardButton(text="📊 Мой профиль", callback_data="profile"),
            InlineKeyboardButton(text="💳 Тарифы",     callback_data="plans"),
        ],
    ])


def ai_info_keyboard(ai_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"▶️ Начать общение", callback_data=f"start_chat:{ai_key}")],
        [InlineKeyboardButton(text="◀️ Назад к выбору",  callback_data="back_to_menu")],
    ])


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")],
        [InlineKeyboardButton(text="📊 Мой профиль",  callback_data="profile")],
    ])


def stop_chat_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛔ Завершить чат", callback_data="stop_chat")],
        [InlineKeyboardButton(text="🏠 Главное меню",  callback_data="back_to_menu")],
    ])


def plans_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Free — бесплатно",    callback_data="plan_info:free")],
        [InlineKeyboardButton(text="🥈 Basic — ~450 ₽/мес",  callback_data="plan_info:basic")],
        [InlineKeyboardButton(text="🥇 Pro — ~900 ₽/мес",    callback_data="plan_info:pro")],
        [InlineKeyboardButton(text="💎 Ultra — ~1800 ₽/мес", callback_data="plan_info:ultra")],
        [InlineKeyboardButton(text="◀️ Назад",               callback_data="back_to_menu")],
    ])


def upgrade_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Улучшить подписку", callback_data="plans")],
        [InlineKeyboardButton(text="🏠 Главное меню",      callback_data="back_to_menu")],
    ])


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика",      callback_data="admin:stats")],
        [InlineKeyboardButton(text="👥 Список юзеров",   callback_data="admin:users")],
        [InlineKeyboardButton(text="🎁 Выдать подписку", callback_data="admin:grant")],
    ])
