from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from keyboards import main_menu_keyboard, ai_info_keyboard, bottom_keyboard
from texts import get_ai_selection_text, AI_DESCRIPTIONS
from database.crud import get_monthly_user_count

router = Router()


@router.message(F.text == "🎨 Картинка")
async def cmd_image_disabled(message: Message):
    await message.answer(
        "🎨 <b>Генерация изображений временно недоступна</b>\n\n"
        "Мы работаем над этой функцией — она появится в ближайшее время.\n\n"
        "Пока что попробуй ChatGPT или Claude 👇",
        reply_markup=bottom_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("menu"))
@router.message(F.text == "🤖 Выбрать нейросеть")
async def cmd_menu(message: Message):
    monthly_users = await get_monthly_user_count()
    await message.answer(
        get_ai_selection_text(monthly_users),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )



@router.callback_query(lambda c: c.data and c.data.startswith("ai:"))
async def cb_select_ai(call: CallbackQuery):
    ai_key = call.data.split(":")[1]
    info = AI_DESCRIPTIONS.get(ai_key)
    if not info:
        await call.answer("Неизвестная нейросеть", show_alert=True)
        return

    text = (
        f"{info['emoji']} <b>{info['name']}</b> ({info['model']}) — {info['tagline']}\n\n"
        f"{info['description']}\n\n"
        f"Нажми <b>«Начать общение»</b> чтобы выбрать режим и начать чат:"
    )
    await call.message.edit_text(text, reply_markup=ai_info_keyboard(ai_key), parse_mode="HTML")
    await call.answer()
