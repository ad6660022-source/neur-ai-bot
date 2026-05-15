import json
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from states import SaveChatState
from modes import AI_MODES, SAVED_CHAT_LIMITS
from database.crud import (
    get_active_subscription,
    get_saved_chats, get_saved_chat, save_chat,
    delete_saved_chat, get_saved_chat_count,
)
from keyboards import saved_chats_keyboard, chat_controls_keyboard, back_to_menu_keyboard

router = Router()

MODEL_DISPLAY = {
    "chatgpt":  "🟢 ChatGPT",
    "claude":   "🟣 Claude",
    "deepseek": "🔵 DeepSeek",
}


# ─────────────────────────────────────────────
#  /chats command & callback
# ─────────────────────────────────────────────
@router.message(Command("chats"))
async def cmd_chats(message: Message):
    chats = await get_saved_chats(message.from_user.id)
    if not chats:
        await message.answer(
            "💾 <b>Сохранённые чаты</b>\n\n"
            "У тебя пока нет сохранённых чатов.\n\n"
            "<i>Во время разговора нажми кнопку «💾 Сохранить»!</i>",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
        return

    sub = await get_active_subscription(message.from_user.id)
    plan = sub.plan if sub else "free"
    limit = SAVED_CHAT_LIMITS.get(plan, 0)
    limit_str = "∞" if limit == -1 else str(limit)

    await message.answer(
        f"💾 <b>Сохранённые чаты</b> ({len(chats)}/{limit_str})\n\n"
        f"Нажми на чат чтобы загрузить · 🗑 чтобы удалить",
        reply_markup=saved_chats_keyboard(chats),
        parse_mode="HTML",
    )


@router.callback_query(lambda c: c.data == "my_chats")
async def cb_my_chats(call: CallbackQuery):
    chats = await get_saved_chats(call.from_user.id)
    if not chats:
        await call.message.edit_text(
            "💾 <b>Сохранённые чаты</b>\n\n"
            "У тебя пока нет сохранённых чатов.\n\n"
            "<i>Во время разговора нажми «💾 Сохранить»!</i>",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
        await call.answer()
        return

    sub = await get_active_subscription(call.from_user.id)
    plan = sub.plan if sub else "free"
    limit = SAVED_CHAT_LIMITS.get(plan, 0)
    limit_str = "∞" if limit == -1 else str(limit)

    await call.message.edit_text(
        f"💾 <b>Сохранённые чаты</b> ({len(chats)}/{limit_str})\n\n"
        f"Нажми на чат чтобы загрузить · 🗑 чтобы удалить",
        reply_markup=saved_chats_keyboard(chats),
        parse_mode="HTML",
    )
    await call.answer()


# ─────────────────────────────────────────────
#  Load saved chat
# ─────────────────────────────────────────────
@router.callback_query(lambda c: c.data and c.data.startswith("load_chat:"))
async def cb_load_chat(call: CallbackQuery, state: FSMContext):
    chat_id = int(call.data.split(":")[1])
    chat = await get_saved_chat(chat_id, call.from_user.id)
    if not chat:
        await call.answer("Чат не найден", show_alert=True)
        return

    history = json.loads(chat.history)
    model = chat.model
    mode = chat.mode

    from states import ChatGPTState, ClaudeState, DeepSeekState
    state_map = {
        "chatgpt":  ChatGPTState.chatting,
        "claude":   ClaudeState.chatting,
        "deepseek": DeepSeekState.chatting,
    }
    fsm_state = state_map.get(model, ChatGPTState.chatting)
    await state.set_state(fsm_state)
    await state.update_data(history=history, mode=mode, model=model)

    mode_info = AI_MODES.get(mode, AI_MODES["default"])
    display = MODEL_DISPLAY.get(model, model)
    msg_count = len([m for m in history if m["role"] == "user"])

    await call.message.edit_text(
        f"💾 Чат <b>«{chat.name}»</b> загружен\n\n"
        f"{display} · {mode_info['emoji']} {mode_info['name']}\n"
        f"Сообщений в истории: {msg_count}\n\n"
        f"<i>Продолжай общение с того места, где остановился!</i>",
        reply_markup=chat_controls_keyboard(model, mode),
        parse_mode="HTML",
    )
    await call.answer("✅ Чат загружен!")


# ─────────────────────────────────────────────
#  Delete saved chat
# ─────────────────────────────────────────────
@router.callback_query(lambda c: c.data and c.data.startswith("del_chat:"))
async def cb_delete_chat(call: CallbackQuery):
    chat_id = int(call.data.split(":")[1])
    deleted = await delete_saved_chat(chat_id, call.from_user.id)
    if not deleted:
        await call.answer("Не найдено", show_alert=True)
        return

    # Refresh list
    chats = await get_saved_chats(call.from_user.id)
    if not chats:
        await call.message.edit_text(
            "💾 <b>Сохранённые чаты</b>\n\nСписок пуст.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        await call.message.edit_reply_markup(reply_markup=saved_chats_keyboard(chats))
    await call.answer("🗑 Удалено")


# ─────────────────────────────────────────────
#  Save current chat (callback from in-chat button)
# ─────────────────────────────────────────────
@router.callback_query(lambda c: c.data == "save_chat")
async def cb_save_chat(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    history = data.get("history", [])
    model = data.get("model", "chatgpt")
    mode = data.get("mode", "default")

    if not history:
        await call.answer("Нечего сохранять — начни чат первым!", show_alert=True)
        return

    sub = await get_active_subscription(call.from_user.id)
    plan = sub.plan if sub else "free"
    limit = SAVED_CHAT_LIMITS.get(plan, 0)

    if limit == 0:
        await call.answer("💾 Сохранение доступно от тарифа Basic 🥈", show_alert=True)
        return

    count = await get_saved_chat_count(call.from_user.id)
    if limit != -1 and count >= limit:
        await call.answer(f"Лимит ({limit}) сохранений исчерпан. Улучши тариф!", show_alert=True)
        return

    # Save current FSM state name to restore it after naming
    current_state = await state.get_state()
    await state.update_data(
        pending_save_model=model,
        pending_save_mode=mode,
        pending_save_history=history,
        pending_save_prev_state=current_state,
    )
    await state.set_state(SaveChatState.waiting_name)

    await call.message.answer(
        "💾 <b>Назови этот чат</b>\n\n"
        "Введи название или отправь /skip для автоматического имени:",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(SaveChatState.waiting_name)
async def handle_save_name(message: Message, state: FSMContext):
    data = await state.get_data()
    model = data.get("pending_save_model", "chatgpt")
    mode = data.get("pending_save_mode", "default")
    history = data.get("pending_save_history", [])
    prev_state = data.get("pending_save_prev_state")

    if message.text and message.text.strip() == "/skip":
        name = f"Чат {datetime.now().strftime('%d.%m %H:%M')}"
    else:
        name = (message.text or "").strip()[:100] or f"Чат {datetime.now().strftime('%d.%m %H:%M')}"

    await save_chat(
        user_id=message.from_user.id,
        name=name,
        model=model,
        mode=mode,
        history=history,
    )

    # Restore previous FSM state
    if prev_state:
        await state.set_state(prev_state)
    await state.update_data(history=history, mode=mode, model=model)

    await message.answer(
        f"✅ Чат сохранён как <b>«{name}»</b>\n\nПродолжай общение:",
        reply_markup=chat_controls_keyboard(model, mode),
        parse_mode="HTML",
    )
