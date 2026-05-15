from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
)
from database.crud import PLAN_STARS


# ─────────────────────────────────────────────
#  Bottom Menu (persistent Reply Keyboard)
# ─────────────────────────────────────────────
def bottom_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🤖 Выбрать нейросеть"),
                KeyboardButton(text="⛔ Завершить чат"),
            ],
            [
                KeyboardButton(text="📊 Мой профиль"),
                KeyboardButton(text="💳 Тарифы"),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
    )


# ─────────────────────────────────────────────
#  Main Menu
# ─────────────────────────────────────────────
def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 ChatGPT",  callback_data="ai:chatgpt"),
            InlineKeyboardButton(text="🟣 Claude",   callback_data="ai:claude"),
            InlineKeyboardButton(text="🔵 DeepSeek", callback_data="ai:deepseek"),
        ],
        [
            InlineKeyboardButton(text="📊 Мой профиль", callback_data="profile"),
            InlineKeyboardButton(text="💳 Тарифы",      callback_data="plans"),
        ],
        [
            InlineKeyboardButton(text="👥 Пригласить друга", callback_data="referral"),
        ],
    ])


def ai_info_keyboard(ai_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать общение", callback_data=f"start_chat:{ai_key}")],
        [InlineKeyboardButton(text="◀️ Назад",          callback_data="back_to_menu")],
    ])


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")],
        [InlineKeyboardButton(text="📊 Мой профиль",  callback_data="profile")],
    ])


def stop_chat_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⛔ Завершить чат", callback_data="stop_chat"),
            InlineKeyboardButton(text="🏠 Меню",          callback_data="back_to_menu"),
        ],
    ])


# ─────────────────────────────────────────────
#  Subscription / Plans
# ─────────────────────────────────────────────
def plans_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Free — бесплатно",    callback_data="plan_info:free")],
        [InlineKeyboardButton(text="🥈 Basic — 399 ⭐",       callback_data="plan_info:basic")],
        [InlineKeyboardButton(text="🥇 Pro — 799 ⭐",         callback_data="plan_info:pro")],
        [InlineKeyboardButton(text="💎 Ultra — 1499 ⭐",      callback_data="plan_info:ultra")],
        [InlineKeyboardButton(text="◀️ Назад",               callback_data="back_to_menu")],
    ])


def buy_plan_keyboard(plan: str) -> InlineKeyboardMarkup:
    stars = PLAN_STARS.get(plan)
    buttons = []
    if stars:
        buttons.append([
            InlineKeyboardButton(
                text=f"⭐ Оплатить {stars} Stars",
                callback_data=f"pay_stars:{plan}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ К тарифам", callback_data="plans")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def upgrade_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Купить Pro — 799 Stars",   callback_data="pay_stars:pro")],
        [InlineKeyboardButton(text="💎 Купить Ultra — 1499 Stars", callback_data="pay_stars:ultra")],
        [InlineKeyboardButton(text="💳 Все тарифы",               callback_data="plans")],
        [InlineKeyboardButton(text="🏠 Главное меню",             callback_data="back_to_menu")],
    ])


# ─────────────────────────────────────────────
#  Admin
# ─────────────────────────────────────────────
def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика",      callback_data="admin:stats")],
        [InlineKeyboardButton(text="👥 Список юзеров",   callback_data="admin:users")],
        [InlineKeyboardButton(text="🎁 Выдать подписку", callback_data="admin:grant")],
        [InlineKeyboardButton(text="🚫 Забанить юзера",  callback_data="admin:ban")],
        [InlineKeyboardButton(text="📣 Рассылка",        callback_data="admin:broadcast")],
    ])
