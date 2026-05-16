from html import escape
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, URLInputFile

from states import ImageState
from services.image_service import generate_image, IMAGE_DAILY_LIMITS, IMAGE_MONTHLY_LIMITS
from database.crud import check_and_increment_image, get_active_subscription
from keyboards import image_keyboard, main_menu_keyboard, upgrade_keyboard, chat_controls_keyboard

router = Router()


@router.message(F.text == "🎨 Картинка")
@router.callback_query(lambda c: c.data == "image_again")
async def cmd_image(event, state: FSMContext):
    is_call = isinstance(event, CallbackQuery)
    msg = event.message if is_call else event

    sub = await get_active_subscription(event.from_user.id)
    if not sub:
        text = "⚠️ Сначала напиши /start"
        if is_call:
            await event.answer(text, show_alert=True)
        else:
            await msg.answer(text)
        return

    daily_limit = IMAGE_DAILY_LIMITS.get(sub.plan, 0)
    monthly_limit = IMAGE_MONTHLY_LIMITS.get(sub.plan, 0)
    if daily_limit == 0 and monthly_limit == 0:
        text = (
            "🎨 <b>Генерация изображений</b>\n\n"
            "Free: 1/месяц · Basic: 10/день · Pro: 10/день · Ultra: 30/день"
        )
        if is_call:
            await event.message.edit_text(text, reply_markup=upgrade_keyboard(), parse_mode="HTML")
            await event.answer()
        else:
            await msg.answer(text, reply_markup=upgrade_keyboard(), parse_mode="HTML")
        return

    # Save current chat state so we can restore it after image generation
    prev_state = await state.get_state()
    prev_data = await state.get_data()
    await state.set_state(ImageState.waiting_prompt)
    await state.update_data(
        _prev_state=prev_state,
        _prev_data=prev_data,
    )

    prompt_msg = (
        "🎨 <b>Генерация изображения</b>\n\n"
        "Опиши что хочешь увидеть — чем подробнее, тем лучше результат.\n\n"
        "<i>Пример: красивый закат над горами, фотореализм, 4K</i>"
    )
    if is_call:
        await event.message.edit_text(prompt_msg, parse_mode="HTML")
        await event.answer()
    else:
        await msg.answer(prompt_msg, parse_mode="HTML")


@router.message(ImageState.waiting_prompt, F.text)
async def handle_image_prompt(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    prompt = message.text.strip()

    allowed, used, limit, period = await check_and_increment_image(user_id)

    if not allowed:
        # Restore previous state before returning
        await _restore_prev_state(state, data)
        reset_text = "в следующем месяце" if period == "месяц" else "завтра"
        await message.answer(
            f"⏰ <b>Лимит изображений исчерпан</b>\n\n"
            f"Использовано за {period}: {used}/{limit}\n"
            f"Лимит сбросится {reset_text}.\n\nУлучшите подписку для большего лимита:",
            reply_markup=upgrade_keyboard(), parse_mode="HTML",
        )
        return

    thinking_msg = await message.answer("🎨 <i>Генерирую изображение... (~15 сек)</i>", parse_mode="HTML")

    try:
        url = await generate_image(prompt)
        await thinking_msg.delete()
        await message.answer_photo(
            photo=URLInputFile(url),
            caption=(
                f"🎨 <b>Готово!</b>\n\n"
                f"<i>{escape(prompt[:100])}</i>\n\n"
                f"📊 Использовано за {period}: {used}/{limit}"
            ),
            reply_markup=image_keyboard(),
            parse_mode="HTML",
        )
    except Exception as e:
        await thinking_msg.delete()
        await message.answer(
            f"❌ <b>Ошибка генерации:</b>\n<code>{escape(str(e)[:200])}</code>\n\nПопробуй другой запрос.",
            reply_markup=main_menu_keyboard(), parse_mode="HTML",
        )

    # Always restore the previous chat state
    await _restore_prev_state(state, data)


async def _restore_prev_state(state: FSMContext, data: dict):
    prev_state = data.get("_prev_state")
    prev_data = data.get("_prev_data") or {}
    if prev_state:
        await state.set_state(prev_state)
        await state.set_data(prev_data)
    else:
        await state.clear()
