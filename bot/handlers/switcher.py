from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from modes import AI_MODES
from states import ChatGPTState, ClaudeState
from keyboards import chat_controls_keyboard, back_to_menu_keyboard, main_menu_keyboard
from database.crud import get_monthly_user_count

router = Router()

_STATE_MAP = {
    "chatgpt": ChatGPTState.chatting,
    "claude":  ClaudeState.chatting,
}

MODEL_DISPLAY = {
    "chatgpt": "🟢 ChatGPT",
    "claude":  "🟣 Claude",
}


@router.callback_query(lambda c: c.data and c.data.startswith("switch_to:"))
async def cb_switch_model(call: CallbackQuery, state: FSMContext):
    new_model = call.data.split(":")[1]
    fsm_state = _STATE_MAP.get(new_model)
    if not fsm_state:
        await call.answer("Неизвестная модель", show_alert=True)
        return

    data = await state.get_data()
    history = data.get("history", [])
    mode = data.get("mode", "default")

    await state.set_state(fsm_state)
    await state.update_data(history=history, mode=mode, model=new_model)

    mode_info = AI_MODES.get(mode, AI_MODES["default"])
    display = MODEL_DISPLAY[new_model]

    await call.message.edit_text(
        f"{display} активен\n"
        f"{mode_info['emoji']} Режим: <b>{mode_info['name']}</b>\n\n"
        f"<i>Контекст диалога сохранён. Продолжай общение!</i>",
        reply_markup=chat_controls_keyboard(new_model, mode),
        parse_mode="HTML",
    )
    await call.answer(f"Переключено на {display}")


@router.callback_query(lambda c: c.data == "stop_chat")
async def cb_stop_chat(call: CallbackQuery, state: FSMContext):
    await state.clear()
    from texts import get_ai_selection_text
    monthly_users = await get_monthly_user_count()
    await call.message.edit_text(
        get_ai_selection_text(monthly_users),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(lambda c: c.data == "back_to_menu")
async def cb_back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    from texts import get_ai_selection_text
    monthly_users = await get_monthly_user_count()
    await call.message.edit_text(
        get_ai_selection_text(monthly_users),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()
