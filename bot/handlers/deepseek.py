from html import escape
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from services.deepseek_service import ask_deepseek
from database.crud import check_and_increment_usage, log_usage
from keyboards import stop_chat_keyboard, upgrade_keyboard, back_to_menu_keyboard

router = Router()


class DeepSeekState(StatesGroup):
    chatting = State()


@router.callback_query(lambda c: c.data == "start_chat:deepseek")
async def cb_start_deepseek(call: CallbackQuery, state: FSMContext):
    await state.set_state(DeepSeekState.chatting)
    await state.update_data(history=[])

    await call.message.edit_text(
        "🔵 <b>DeepSeek (V3)</b>\n\n"
        "Чат активен! Напиши свой вопрос.\n\n"
        "<i>DeepSeek специализируется на математике,\n"
        "логике и программировании.\n"
        "Нажми «Завершить чат» чтобы выйти.</i>",
        reply_markup=stop_chat_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.message(DeepSeekState.chatting, F.text)
async def handle_deepseek_message(message: Message, state: FSMContext):
    user_id = message.from_user.id

    allowed, used_m, limit_m, used_d, limit_d = await check_and_increment_usage(user_id, "deepseek")

    if not allowed:
        if limit_m == 0:
            await message.answer(
                "🔵 <b>DeepSeek</b> недоступен на вашем тарифе.\n\n"
                "Улучшите подписку чтобы получить доступ:",
                reply_markup=upgrade_keyboard(),
                parse_mode="HTML",
            )
        elif limit_d != -1 and used_d >= limit_d:
            await message.answer(
                f"⏰ <b>Дневной лимит DeepSeek исчерпан</b>\n\n"
                f"Использовано сегодня: {used_d}/{limit_d}\n"
                f"Лимит сбросится завтра.\n\n"
                f"Улучшите подписку для большего дневного лимита:",
                reply_markup=upgrade_keyboard(),
                parse_mode="HTML",
            )
        else:
            await message.answer(
                f"⚠️ <b>Месячный лимит DeepSeek исчерпан</b>\n\n"
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
    thinking_msg = await message.answer("🔵 <i>DeepSeek обрабатывает...</i>", parse_mode="HTML")

    try:
        response, prompt_tokens, completion_tokens = await ask_deepseek(history)
        history.append({"role": "assistant", "content": response})

        if len(history) > 20:
            history = history[-20:]

        await state.update_data(history=history)
        await log_usage(user_id, "deepseek", prompt_tokens, completion_tokens, True)

        limit_m_str = "∞" if limit_m == -1 else str(limit_m)
        limit_d_str = "∞" if limit_d == -1 else str(limit_d)
        footer = f"\n\n<i>🔵 DeepSeek · {used_m}/{limit_m_str} мес · {used_d}/{limit_d_str} день</i>"

        await thinking_msg.delete()
        await message.answer(
            escape(response) + footer,
            reply_markup=stop_chat_keyboard(),
            parse_mode="HTML",
        )

    except Exception as e:
        await log_usage(user_id, "deepseek", 0, 0, False)
        await thinking_msg.delete()
        await message.answer(
            f"❌ <b>Ошибка DeepSeek:</b>\n<code>{escape(str(e)[:200])}</code>\n\n"
            f"Попробуй ещё раз или вернись в меню.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
