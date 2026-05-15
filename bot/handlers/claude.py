from html import escape
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from services.claude_service import ask_claude
from database.crud import check_and_increment_usage, log_usage
from keyboards import stop_chat_keyboard, upgrade_keyboard, back_to_menu_keyboard

router = Router()


class ClaudeState(StatesGroup):
    chatting = State()


@router.callback_query(lambda c: c.data == "start_chat:claude")
async def cb_start_claude(call: CallbackQuery, state: FSMContext):
    await state.set_state(ClaudeState.chatting)
    await state.update_data(history=[])

    await call.message.edit_text(
        "🟣 <b>Claude (Sonnet 4.6)</b>\n\n"
        "Чат активен! Напиши свой вопрос.\n\n"
        "<i>Claude отлично справляется с анализом больших текстов\n"
        "и сложными исследовательскими задачами.\n"
        "Нажми «Завершить чат» чтобы выйти.</i>",
        reply_markup=stop_chat_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.message(ClaudeState.chatting, F.text)
async def handle_claude_message(message: Message, state: FSMContext):
    user_id = message.from_user.id

    allowed, used_m, limit_m, used_d, limit_d = await check_and_increment_usage(user_id, "claude")

    if not allowed:
        if limit_m == 0:
            await message.answer(
                "🟣 <b>Claude</b> доступен только с тарифами Pro и Ultra.\n\n"
                "Улучшите подписку чтобы получить доступ:",
                reply_markup=upgrade_keyboard(),
                parse_mode="HTML",
            )
        elif limit_d != -1 and used_d >= limit_d:
            await message.answer(
                f"⏰ <b>Дневной лимит Claude исчерпан</b>\n\n"
                f"Использовано сегодня: {used_d}/{limit_d}\n"
                f"Лимит сбросится завтра.\n\n"
                f"Улучшите подписку для большего дневного лимита:",
                reply_markup=upgrade_keyboard(),
                parse_mode="HTML",
            )
        else:
            await message.answer(
                f"⚠️ <b>Месячный лимит Claude исчерпан</b>\n\n"
                f"Использовано: {used_m}/{limit_m} запросов.\n"
                f"Сбросится через ~30 дней.\n\n"
                f"Улучшите подписку для большего лимита:",
                reply_markup=upgrade_keyboard(),
                parse_mode="HTML",
            )
        return

    data = await state.get_data()
    history = data.get("history", [])
    history.append({"role": "user", "content": message.text})

    await message.bot.send_chat_action(message.chat.id, "typing")
    thinking_msg = await message.answer("🟣 <i>Claude анализирует...</i>", parse_mode="HTML")

    try:
        response, prompt_tokens, completion_tokens = await ask_claude(history)
        history.append({"role": "assistant", "content": response})

        if len(history) > 20:
            history = history[-20:]

        await state.update_data(history=history)
        await log_usage(user_id, "claude", prompt_tokens, completion_tokens, True)

        limit_m_str = "∞" if limit_m == -1 else str(limit_m)
        limit_d_str = "∞" if limit_d == -1 else str(limit_d)
        footer = f"\n\n<i>🟣 Claude · {used_m}/{limit_m_str} мес · {used_d}/{limit_d_str} день</i>"

        await thinking_msg.delete()
        await message.answer(
            escape(response) + footer,
            reply_markup=stop_chat_keyboard(),
            parse_mode="HTML",
        )

    except Exception as e:
        await log_usage(user_id, "claude", 0, 0, False)
        await thinking_msg.delete()
        await message.answer(
            f"❌ <b>Ошибка Claude:</b>\n<code>{escape(str(e)[:200])}</code>\n\n"
            f"Попробуй ещё раз или вернись в меню.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
