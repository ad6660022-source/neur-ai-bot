from html import escape
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, URLInputFile

from states import ImageState
from services.image_service import generate_image, IMAGE_DAILY_LIMITS
from database.crud import check_and_increment_image, get_active_subscription
from keyboards import image_keyboard, main_menu_keyboard, upgrade_keyboard

router = Router()


@router.message(F.text == "🎨 Картинка")
@router.callback_query(lambda c: c.data == "image_again")
async def cmd_image(event, state: FSMContext):
    is_call = isinstance(event, CallbackQuery)
    msg = event.message if is_call else event

    # Check access
    sub = await get_active_subscription(event.from_user.id)
    if not sub:
        text = "⚠️ Сначала напиши /start"
        if is_call:
            await event.answer(text, show_alert=True)
        else:
            await msg.answer(text)
        return

    limit = IMAGE_DAILY_LIMITS.get(sub.plan, 0)
    if limit == 0:
        text = (
            "🎨 <b>Генерация изображений</b>\n\n"
            "Доступна с тарифа <b>Basic</b> и выше.\n\n"
            "Free: нет · Basic: 3/день · Pro: 10/день · Ultra: 30/день"
        )
        if is_call:
            await event.message.edit_text(text, reply_markup=upgrade_keyboard(), parse_mode="HTML")
            await event.answer()
        else:
            await msg.answer(text, reply_markup=upgrade_keyboard(), parse_mode="HTML")
        return

    await state.set_state(ImageState.waiting_prompt)

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
    prompt = message.text.strip()

    allowed, used, limit = await check_and_increment_image(user_id)

    if not allowed:
        await state.clear()
        await message.answer(
            f"⏰ <b>Дневной лимит изображений исчерпан</b>\n\n"
            f"Использовано сегодня: {used}/{limit}\n"
            f"Лимит сбросится завтра.\n\nУлучшите подписку для большего лимита:",
            reply_markup=upgrade_keyboard(), parse_mode="HTML",
        )
        return

    await state.update_data(last_prompt=prompt)

    thinking_msg = await message.answer("🎨 <i>Генерирую изображение... (~15 сек)</i>", parse_mode="HTML")

    try:
        url = await generate_image(prompt)
        await thinking_msg.delete()
        await message.answer_photo(
            photo=URLInputFile(url),
            caption=(
                f"🎨 <b>Готово!</b>\n\n"
                f"<i>{escape(prompt[:100])}</i>\n\n"
                f"📊 Использовано сегодня: {used}/{limit}"
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

    await state.clear()
