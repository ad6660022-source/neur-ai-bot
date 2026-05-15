from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from database.crud import get_or_create_user, get_active_subscription, get_user, grant_trial
from keyboards import main_menu_keyboard, back_to_menu_keyboard, bottom_keyboard
from texts import get_welcome_text, get_usage_text, get_referral_text

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    referred_by = None

    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            rid = int(args[1][4:])
            if rid != message.from_user.id:
                referred_by = rid
        except ValueError:
            pass

    user, is_new = await get_or_create_user(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        last_name=message.from_user.last_name,
        language_code=message.from_user.language_code,
        referred_by=referred_by,
    )

    if is_new:
        # Give every new user a 3-day Pro trial
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


@router.callback_query(lambda c: c.data == "referral")
async def cb_referral(call: CallbackQuery, bot: Bot):
    user = await get_user(call.from_user.id)
    if not user:
        await call.answer("Ошибка", show_alert=True)
        return

    bot_info = await bot.get_me()
    ref_code = user.referral_code or str(user.telegram_id)

    from database.db import async_session
    from database.models import User
    from sqlalchemy import select, func
    async with async_session() as session:
        count = (await session.execute(
            select(func.count(User.id)).where(User.referred_by == user.telegram_id)
        )).scalar() or 0

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
    ])
    await call.message.edit_text(
        get_referral_text(ref_code, bot_info.username, count),
        reply_markup=kb,
        parse_mode="HTML",
    )
    await call.answer()
