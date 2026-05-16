from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
    WebAppInfo,
)
from database.crud import PLAN_STARS
from modes import AI_MODES

MODEL_EMOJI = {"chatgpt": "🟢", "claude": "🟣"}
MODEL_NAME  = {"chatgpt": "ChatGPT", "claude": "Claude"}


# ─────────────────────────────────────────────
#  Bottom persistent keyboard
# ─────────────────────────────────────────────
def bottom_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🤖 Выбрать нейросеть")],
            [KeyboardButton(text="📊 Мой профиль"),       KeyboardButton(text="💳 Тарифы")],
            [KeyboardButton(text="💬 Поддержка")],
        ],
        resize_keyboard=True,
        persistent=True,
    )


# ─────────────────────────────────────────────
#  Main menu
# ─────────────────────────────────────────────
def main_menu_keyboard() -> InlineKeyboardMarkup:
    from config import settings
    rows = [
        [
            InlineKeyboardButton(text="🟢 ChatGPT", callback_data="ai:chatgpt"),
            InlineKeyboardButton(text="🟣 Claude",  callback_data="ai:claude"),
        ],
        [
            InlineKeyboardButton(text="📊 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="💳 Тарифы",  callback_data="plans"),
            InlineKeyboardButton(text="💾 Чаты",    callback_data="my_chats"),
        ],
    ]
    if settings.WEBAPP_URL:
        rows.append([
            InlineKeyboardButton(text="🌐 Открыть Mini App", web_app=WebAppInfo(url=settings.WEBAPP_URL)),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def channel_bonus_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на @neur_ai_pub", url="https://t.me/neur_ai_pub")],
        [InlineKeyboardButton(text="✅ Я подписался — получить +10 запросов", callback_data="check_channel_sub")],
        [InlineKeyboardButton(text="💳 Все тарифы", callback_data="plans")],
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


# ─────────────────────────────────────────────
#  Mode selection
# ─────────────────────────────────────────────
def mode_selection_keyboard(ai_key: str) -> InlineKeyboardMarkup:
    items = list(AI_MODES.items())
    rows = []
    for i in range(0, len(items), 2):
        row = []
        for mode_key, mode in items[i:i + 2]:
            row.append(InlineKeyboardButton(
                text=f"{mode['emoji']} {mode['name']}",
                callback_data=f"set_mode:{ai_key}:{mode_key}",
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"ai:{ai_key}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ─────────────────────────────────────────────
#  In-chat controls
# ─────────────────────────────────────────────
def chat_controls_keyboard(current_model: str, mode: str = "default") -> InlineKeyboardMarkup:
    switch_row = []
    for model, emoji in MODEL_EMOJI.items():
        if model != current_model:
            switch_row.append(InlineKeyboardButton(
                text=f"→ {emoji} {MODEL_NAME[model]}",
                callback_data=f"switch_to:{model}",
            ))

    mode_info = AI_MODES.get(mode, AI_MODES["default"])
    return InlineKeyboardMarkup(inline_keyboard=[
        switch_row,
        [
            InlineKeyboardButton(text=f"{mode_info['emoji']} Режим", callback_data=f"change_mode:{current_model}"),
            InlineKeyboardButton(text="💾 Сохранить", callback_data="save_chat"),
        ],
        [
            InlineKeyboardButton(text="⛔ Стоп", callback_data="stop_chat"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_menu"),
        ],
    ])


def stop_chat_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⛔ Завершить чат", callback_data="stop_chat"),
            InlineKeyboardButton(text="🏠 Меню",          callback_data="back_to_menu"),
        ],
    ])


def image_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Ещё вариант", callback_data="image_again")],
        [InlineKeyboardButton(text="🏠 Меню",        callback_data="back_to_menu")],
    ])


# ─────────────────────────────────────────────
#  Plans / payment
# ─────────────────────────────────────────────
def plans_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Free — бесплатно",   callback_data="plan_info:free")],
        [InlineKeyboardButton(text=f"🥈 Basic — {PLAN_STARS['basic']} ⭐", callback_data="plan_info:basic")],
        [InlineKeyboardButton(text=f"🥇 Pro — {PLAN_STARS['pro']} ⭐",     callback_data="plan_info:pro")],
        [InlineKeyboardButton(text=f"💎 Ultra — {PLAN_STARS['ultra']} ⭐", callback_data="plan_info:ultra")],
        [InlineKeyboardButton(text="◀️ Назад",              callback_data="back_to_menu")],
    ])


def buy_plan_keyboard(plan: str) -> InlineKeyboardMarkup:
    stars = PLAN_STARS.get(plan)
    rows = []
    if stars:
        rows.append([InlineKeyboardButton(
            text=f"⭐ Оплатить {stars} Stars",
            callback_data=f"pay_stars:{plan}",
        )])
    rows.append([InlineKeyboardButton(text="◀️ К тарифам", callback_data="plans")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def upgrade_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⭐ Pro — {PLAN_STARS['pro']} Stars",   callback_data="pay_stars:pro")],
        [InlineKeyboardButton(text=f"💎 Ultra — {PLAN_STARS['ultra']} Stars", callback_data="pay_stars:ultra")],
        [InlineKeyboardButton(text="💳 Все тарифы", callback_data="plans")],
        [InlineKeyboardButton(text="🏠 Меню",       callback_data="back_to_menu")],
    ])


# ─────────────────────────────────────────────
#  Saved chats list
# ─────────────────────────────────────────────
def saved_chats_keyboard(chats: list) -> InlineKeyboardMarkup:
    rows = []
    for chat in chats[:15]:
        emoji = MODEL_EMOJI.get(chat.model, "🤖")
        mode_info = AI_MODES.get(chat.mode, AI_MODES["default"])
        label = f"{emoji} {mode_info['emoji']} {chat.name}"
        rows.append([
            InlineKeyboardButton(text=label[:35],       callback_data=f"load_chat:{chat.id}"),
            InlineKeyboardButton(text="🗑",              callback_data=f"del_chat:{chat.id}"),
        ])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ─────────────────────────────────────────────
#  Admin
# ─────────────────────────────────────────────
def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика",      callback_data="admin:stats")],
        [InlineKeyboardButton(text="👥 Список юзеров",   callback_data="admin:users")],
        [InlineKeyboardButton(text="🎁 Выдать подписку", callback_data="admin:grant")],
        [InlineKeyboardButton(text="🚫 Бан / Разбан",    callback_data="admin:ban")],
        [InlineKeyboardButton(text="📣 Рассылка",        callback_data="admin:broadcast")],
    ])
