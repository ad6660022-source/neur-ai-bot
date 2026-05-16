from html import escape
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import settings
from states import SupportState
from keyboards import back_to_menu_keyboard

router = Router()

_MENU_BUTTONS = {"🤖 Выбрать нейросеть", "📊 Мой профиль", "💳 Тарифы", "💬 Поддержка"}


@router.message(F.text == "💬 Поддержка")
@router.message(Command("support"))
async def cmd_support(message: Message, state: FSMContext):
    await state.set_state(SupportState.waiting_message)
    await message.answer(
        "💬 <b>Поддержка NEUR AI</b>\n\n"
        "Опиши свой вопрос или проблему — мы ответим в течение 24 часов.\n\n"
        "/cancel — отмена",
        parse_mode="HTML",
    )


@router.message(SupportState.waiting_message)
async def handle_support_message(message: Message, state: FSMContext):
    text = message.text or ""

    if text.startswith("/") or text in _MENU_BUTTONS:
        await state.clear()
        await message.answer("Отменено. Используй /menu для навигации.")
        return

    await state.clear()

    user = message.from_user
    user_info = f"@{user.username}" if user.username else f"ID: {user.id}"

    for admin_id in settings.admin_list:
        try:
            await message.bot.send_message(
                admin_id,
                f"📩 <b>Обращение в поддержку</b>\n\n"
                f"👤 <b>{escape(user.first_name)}</b> {escape(user_info)}\n"
                f"🆔 <code>{user.id}</code>\n\n"
                f"💬 {escape(text)}\n\n"
                f"<i>Ответить: /reply {user.id} &lt;текст&gt;</i>",
                parse_mode="HTML",
            )
        except Exception:
            pass

    await message.answer(
        "✅ <b>Обращение отправлено!</b>\n\n"
        "Мы ответим в течение 24 часов.\n\n"
        "Используй /menu для продолжения работы.",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )
