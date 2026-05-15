from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from modes import AI_MODES
from states import ChatGPTState, ClaudeState, DeepSeekState
from keyboards import mode_selection_keyboard, chat_controls_keyboard

router = Router()

MODEL_DISPLAY = {
    "chatgpt": "🟢 ChatGPT (GPT-4o)",
    "claude":  "🟣 Claude (Sonnet 4.6)",
    "deepseek": "🔵 DeepSeek (V3)",
}

_STATE_MAP = {
    "chatgpt":  ChatGPTState.chatting,
    "claude":   ClaudeState.chatting,
    "deepseek": DeepSeekState.chatting,
}


@router.callback_query(lambda c: c.data and c.data.startswith("start_chat:"))
async def cb_start_chat(call: CallbackQuery):
    ai_key = call.data.split(":")[1]
    display = MODEL_DISPLAY.get(ai_key, ai_key)

    await call.message.edit_text(
        f"{display}\n\n"
        f"<b>Выбери режим работы:</b>\n\n"
        f"🤖 Стандартный — универсальный ответ\n"
        f"👨‍💻 Программист — код и технические объяснения\n"
        f"✍️ Копирайтер — тексты и маркетинг\n"
        f"🎓 Учитель — простые объяснения с примерами\n"
        f"🔬 Аналитик — структурированные выводы\n"
        f"🎭 Творческий — нестандартные идеи\n"
        f"📊 Бизнес — практичные советы с ROI",
        reply_markup=mode_selection_keyboard(ai_key),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("set_mode:"))
async def cb_set_mode(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    ai_key, mode_key = parts[1], parts[2]

    fsm_state = _STATE_MAP.get(ai_key)
    if not fsm_state:
        await call.answer("Ошибка модели", show_alert=True)
        return

    # Preserve existing history when changing mode mid-chat
    data = await state.get_data()
    history = data.get("history", [])

    await state.set_state(fsm_state)
    await state.update_data(history=history, mode=mode_key, model=ai_key)

    mode_info = AI_MODES.get(mode_key, AI_MODES["default"])
    display = MODEL_DISPLAY.get(ai_key, ai_key)

    await call.message.edit_text(
        f"{display}\n"
        f"{mode_info['emoji']} Режим: <b>{mode_info['name']}</b>\n\n"
        f"<i>Чат активен! Напиши свой вопрос.\n"
        f"{'Контекст предыдущего чата сохранён.' if history else 'Начинаем с чистого листа.'}</i>",
        reply_markup=chat_controls_keyboard(ai_key, mode_key),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("change_mode:"))
async def cb_change_mode(call: CallbackQuery):
    ai_key = call.data.split(":")[1]
    display = MODEL_DISPLAY.get(ai_key, ai_key)

    await call.message.edit_text(
        f"{display} — смена режима\n\n<b>Выбери новый режим:</b>",
        reply_markup=mode_selection_keyboard(ai_key),
        parse_mode="HTML",
    )
    await call.answer()
