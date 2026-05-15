from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from database.crud import get_or_create_user, get_active_subscription, get_user, grant_trial
from keyboards import main_menu_keyboard, back_to_menu_keyboard, bottom_keyboard
from texts import get_welcome_text, get_usage_text

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user, is_new = await get_or_create_user(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        last_name=message.from_user.last_name,
        language_code=message.from_user.language_code,
    )

    if is_new:
        await grant_trial(message.from_user.id)

    await message.answer(
        "👇 Используй меню ниже для навигации:",
        reply_markup=bottom_keyboard(),
    )

    welcome = get_welcome_text(message.from_user.first_name, is_new=is_new)
    await message.answer(
        welcome,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("profile"))
@router.message(F.text == "📊 Мой профиль")
async def cmd_profile(message: Message):
    sub = await get_active_subscription(message.from_user.id)
    user = await get_user(message.from_user.id)
    if not sub:
        await message.answer("⚠️ Профиль не найден. Напиши /start")
        return
    await message.answer(
        get_usage_text(sub, user),
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(lambda c: c.data == "profile")
async def cb_profile(call: CallbackQuery):
    sub = await get_active_subscription(call.from_user.id)
    user = await get_user(call.from_user.id)
    if not sub:
        await call.answer("Профиль не найден", show_alert=True)
        return
    await call.message.edit_text(
        get_usage_text(sub, user),
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()
