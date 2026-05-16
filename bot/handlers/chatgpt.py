from html import escape
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from states import ChatGPTState
from modes import AI_MODES
from services.openai_service import ask_chatgpt, ask_chatgpt_with_image
from services.whisper_service import transcribe_voice
from database.crud import check_and_increment_usage, log_usage, check_and_grant_channel_bonus
from keyboards import chat_controls_keyboard, upgrade_keyboard, back_to_menu_keyboard, channel_bonus_keyboard
from utils import markdown_to_html

router = Router()

_BONUS_TEXT = (
    "\n\n📢 <b>Подпишись на @neur_ai_pub</b> и получи <b>+10 запросов</b> бесплатно!"
)


async def _process_chatgpt(message: Message, state: FSMContext, text: str):
    user_id = message.from_user.id
    data = await state.get_data()
    mode = data.get("mode", "default")

    allowed, used_m, limit_m, used_d, limit_d = await check_and_increment_usage(user_id, "chatgpt")

    if not allowed:
        if limit_m == 0:
            await message.answer(
                "🟢 <b>ChatGPT</b> недоступен на вашем тарифе.\n\nУлучшите подписку:",
                reply_markup=upgrade_keyboard(), parse_mode="HTML",
            )
        elif limit_d != -1 and used_d >= limit_d:
            await message.answer(
                f"⏰ <b>Дневной лимит ChatGPT исчерпан</b>\n\n"
                f"Использовано сегодня: {used_d}/{limit_d}\n"
                f"Лимит сбросится завтра.{_BONUS_TEXT}",
                reply_markup=channel_bonus_keyboard(), parse_mode="HTML",
            )
        else:
            await message.answer(
                f"⚠️ <b>Месячный лимит ChatGPT исчерпан</b>\n\n"
                f"Использовано: {used_m}/{limit_m} запросов.{_BONUS_TEXT}",
                reply_markup=channel_bonus_keyboard(), parse_mode="HTML",
            )
        return

    history = data.get("history", [])
    history.append({"role": "user", "content": text})

    await message.bot.send_chat_action(message.chat.id, "typing")
    thinking_msg = await message.answer("🟢 <i>ChatGPT думает...</i>", parse_mode="HTML")

    try:
        mode_prompt = AI_MODES.get(mode, AI_MODES["default"])["prompt"]
        response, prompt_tokens, completion_tokens = await ask_chatgpt(history, mode_prompt)
        history.append({"role": "assistant", "content": response})
        if len(history) > 20:
            history = history[-20:]

        await state.update_data(history=history, mode=mode, model="chatgpt")
        await log_usage(user_id, "chatgpt", prompt_tokens, completion_tokens, True)

        lm = "∞" if limit_m == -1 else str(limit_m)
        ld = "∞" if limit_d == -1 else str(limit_d)

        warning = ""
        if limit_m != -1 and limit_m > 0 and used_m >= int(limit_m * 0.8):
            warning = f"\n⚠️ <i>Осталось {limit_m - used_m} из {limit_m} запросов в месяце</i>"

        footer = f"\n\n<i>🟢 {used_m}/{lm} мес · {used_d}/{ld} день</i>{warning}"

        await thinking_msg.delete()
        await message.answer(
            markdown_to_html(response) + footer,
            reply_markup=chat_controls_keyboard("chatgpt", mode),
            parse_mode="HTML",
        )
    except Exception as e:
        await log_usage(user_id, "chatgpt", 0, 0, False)
        await thinking_msg.delete()
        await message.answer(
            f"❌ <b>Ошибка ChatGPT:</b>\n<code>{escape(str(e)[:200])}</code>\n\nПопробуй ещё раз.",
            reply_markup=back_to_menu_keyboard(), parse_mode="HTML",
        )


@router.callback_query(lambda c: c.data == "check_channel_sub")
async def cb_check_channel_sub(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    try:
        member = await bot.get_chat_member(chat_id="@neur_ai_pub", user_id=user_id)
        is_sub = member.status in ("member", "administrator", "creator", "restricted")
    except Exception:
        await call.answer("❌ Не удалось проверить подписку. Попробуй позже.", show_alert=True)
        return

    if not is_sub:
        await call.answer("❌ Ты ещё не подписан на @neur_ai_pub", show_alert=True)
        return

    granted = await check_and_grant_channel_bonus(user_id)
    if granted:
        await call.answer("✅ +10 запросов ChatGPT начислено!", show_alert=True)
        await call.message.edit_text(
            "🎉 <b>Бонус получен!</b>\n\n"
            "+10 запросов ChatGPT добавлено к твоему балансу.\n\n"
            "Подписка на @neur_ai_pub даёт доступ к новостям и обновлениям NEUR AI.\n\n"
            "Возвращайся к общению!",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        await call.answer("Бонус уже был получен ранее.", show_alert=True)


@router.message(ChatGPTState.chatting, F.text)
async def handle_chatgpt_message(message: Message, state: FSMContext):
    await _process_chatgpt(message, state, message.text)


@router.message(ChatGPTState.chatting, F.photo)
async def handle_chatgpt_photo(message: Message, state: FSMContext, bot: Bot):
    thinking_msg = await message.answer("🟢 <i>ChatGPT анализирует изображение...</i>", parse_mode="HTML")
    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_bytes_io = await bot.download_file(file.file_path)
        image_bytes = file_bytes_io.read()
        caption = message.caption or "Что на изображении?"
        await thinking_msg.delete()
    except Exception as e:
        await thinking_msg.delete()
        await message.answer(f"❌ Не удалось загрузить изображение: {escape(str(e)[:100])}")
        return

    user_id = message.from_user.id
    data = await state.get_data()
    mode = data.get("mode", "default")

    allowed, used_m, limit_m, used_d, limit_d = await check_and_increment_usage(user_id, "chatgpt")
    if not allowed:
        if limit_m == 0:
            await message.answer("🟢 <b>ChatGPT</b> недоступен на вашем тарифе.", reply_markup=upgrade_keyboard(), parse_mode="HTML")
        elif limit_d != -1 and used_d >= limit_d:
            await message.answer(f"⏰ <b>Дневной лимит ChatGPT исчерпан</b> ({used_d}/{limit_d}){_BONUS_TEXT}", reply_markup=channel_bonus_keyboard(), parse_mode="HTML")
        else:
            await message.answer(f"⚠️ <b>Месячный лимит ChatGPT исчерпан</b> ({used_m}/{limit_m}){_BONUS_TEXT}", reply_markup=channel_bonus_keyboard(), parse_mode="HTML")
        return

    history = data.get("history", [])
    thinking_msg = await message.answer("🟢 <i>ChatGPT думает...</i>", parse_mode="HTML")
    try:
        mode_prompt = AI_MODES.get(mode, AI_MODES["default"])["prompt"]
        response, prompt_tokens, completion_tokens = await ask_chatgpt_with_image(image_bytes, caption, history, mode_prompt)
        history.append({"role": "user", "content": f"[Изображение] {caption}"})
        history.append({"role": "assistant", "content": response})
        if len(history) > 20:
            history = history[-20:]
        await state.update_data(history=history, mode=mode, model="chatgpt")
        await log_usage(user_id, "chatgpt", prompt_tokens, completion_tokens, True)
        lm = "∞" if limit_m == -1 else str(limit_m)
        ld = "∞" if limit_d == -1 else str(limit_d)
        footer = f"\n\n<i>🟢 {used_m}/{lm} мес · {used_d}/{ld} день</i>"
        await thinking_msg.delete()
        await message.answer(markdown_to_html(response) + footer, reply_markup=chat_controls_keyboard("chatgpt", mode), parse_mode="HTML")
    except Exception as e:
        await log_usage(user_id, "chatgpt", 0, 0, False)
        await thinking_msg.delete()
        await message.answer(f"❌ <b>Ошибка ChatGPT:</b>\n<code>{escape(str(e)[:200])}</code>", reply_markup=back_to_menu_keyboard(), parse_mode="HTML")


@router.message(ChatGPTState.chatting, F.voice)
async def handle_chatgpt_voice(message: Message, state: FSMContext, bot: Bot):
    thinking_msg = await message.answer("🎙 <i>Распознаю голос...</i>", parse_mode="HTML")
    try:
        file = await bot.get_file(message.voice.file_id)
        file_bytes = await bot.download_file(file.file_path)
        text = await transcribe_voice(file_bytes.read())
        await thinking_msg.delete()
        await message.answer(f"🎙 <i>Распознано:</i> {escape(text)}", parse_mode="HTML")
    except Exception as e:
        await thinking_msg.delete()
        await message.answer(f"❌ Не удалось распознать голос: {escape(str(e)[:100])}")
        return
    await _process_chatgpt(message, state, text)
