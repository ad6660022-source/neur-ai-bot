from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from services.openai_service import ask_chatgpt
from database.crud import check_and_increment_usage, log_usage
from keyboards import stop_chat_keyboard, upgrade_keyboard, back_to_menu_keyboard

router = Router()


class ChatGPTState(StatesGroup):
    chatting = State()


@router.callback_query(lambda c: c.data == "start_chat:chatgpt")
async def cb_start_chatgpt(call: CallbackQuery, state: FSMContext):
    await state.set_state(ChatGPTState.chatting)
    await state.update_data(history=[])

    await call.message.edit_text(
        "🟢 <b>ChatGPT (GPT-4o)</b>\n\n"
        "Чат активен! Напиши свой вопрос.\n\n"
        "<i>Я помню контекст всего нашего разговора.\n"
        "Нажми «Завершить чат» чтобы вернуться в меню.</i>",
        reply_markup=stop_chat_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(lambda c: c.data == "stop_chat")
async def cb_stop_chat(call: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    await call.message.edit_text(
        "✅ Чат завершён.\n\nВыбери нейросеть или раздел:",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.message(ChatGPTState.chatting, F.text)
async def handle_chatgpt_message(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Check usage limit
    allowed, used, limit = await check_and_increment_usage(user_id, "chatgpt")

    if not allowed:
        if limit == 0:
            await message.answer(
                "🟢 <b>ChatGPT</b> недоступен на вашем тарифе.\n\n"
                "Улучшите подписку чтобы получить доступ:",
                reply_markup=upgrade_keyboard(),
                parse_mode="HTML",
            )
        else:
            await message.answer(
                f"⚠️ <b>Лимит ChatGPT исчерпан</b>\n\n"
                f"Вы использовали {used}/{limit} запросов в этом месяце.\n"
                f"Лимит сбросится через ~30 дней.\n\n"
                f"Улучшите подписку для большего числа запросов:",
                reply_markup=upgrade_keyboard(),
                parse_mode="HTML",
            )
        return

    # Get conversation history
    data = await state.get_data()
    history = data.get("history", [])
    history.append({"role": "user", "content": message.text})

    # Show typing
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Call API
    thinking_msg = await message.answer("🟢 <i>ChatGPT думает...</i>", parse_mode="HTML")

    try:
        response, prompt_tokens, completion_tokens = await ask_chatgpt(history)
        history.append({"role": "assistant", "content": response})

        # Keep last 20 messages to avoid context overflow
        if len(history) > 20:
            history = history[-20:]

        await state.update_data(history=history)
        await log_usage(user_id, "chatgpt", prompt_tokens, completion_tokens, True)

        limit_str = "∞" if limit == -1 else str(limit)
        footer = f"\n\n<i>🟢 ChatGPT · {used}/{limit_str} запросов</i>"

        await thinking_msg.delete()
        await message.answer(
            response + footer,
            reply_markup=stop_chat_keyboard(),
            parse_mode="HTML",
        )

    except Exception as e:
        await log_usage(user_id, "chatgpt", 0, 0, False)
        await thinking_msg.delete()
        await message.answer(
            f"❌ <b>Ошибка ChatGPT:</b>\n<code>{str(e)[:200]}</code>\n\n"
            f"Попробуй ещё раз или вернись в меню.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
