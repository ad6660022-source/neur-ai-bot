from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import settings
from database.crud import get_all_users, get_stats, set_subscription, get_user
from keyboards import admin_keyboard, back_to_menu_keyboard

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_list


class AdminGrantState(StatesGroup):
    waiting_user_id = State()
    waiting_plan = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    stats = await get_stats()
    text = (
        f"🔧 <b>Панель администратора</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"📊 Всего запросов: <b>{stats['total_requests']}</b>\n\n"
        f"🟢 ChatGPT: {stats['chatgpt_requests']}\n"
        f"🟣 Claude:   {stats['claude_requests']}\n"
        f"🔵 DeepSeek: {stats['deepseek_requests']}"
    )
    await message.answer(text, reply_markup=admin_keyboard(), parse_mode="HTML")


@router.callback_query(lambda c: c.data == "admin:stats")
async def cb_admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    stats = await get_stats()
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"📨 Всего запросов: <b>{stats['total_requests']}</b>\n\n"
        f"🟢 ChatGPT: {stats['chatgpt_requests']}\n"
        f"🟣 Claude:   {stats['claude_requests']}\n"
        f"🔵 DeepSeek: {stats['deepseek_requests']}"
    )
    await call.message.edit_text(text, reply_markup=admin_keyboard(), parse_mode="HTML")
    await call.answer()


@router.callback_query(lambda c: c.data == "admin:users")
async def cb_admin_users(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    users = await get_all_users()
    if not users:
        await call.answer("Пользователей нет", show_alert=True)
        return

    lines = []
    for u in users[:20]:
        name = u.first_name
        uname = f"@{u.username}" if u.username else "—"
        lines.append(f"• <b>{name}</b> {uname} — <code>{u.telegram_id}</code>")

    text = f"👥 <b>Последние пользователи</b> ({len(users)} всего):\n\n" + "\n".join(lines)
    await call.message.edit_text(text, reply_markup=admin_keyboard(), parse_mode="HTML")
    await call.answer()


@router.callback_query(lambda c: c.data == "admin:grant")
async def cb_admin_grant(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminGrantState.waiting_user_id)
    await call.message.answer(
        "🎁 <b>Выдача подписки</b>\n\n"
        "Введи Telegram ID пользователя:",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(AdminGrantState.waiting_user_id)
async def admin_grant_user_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введи число.")
        return

    user = await get_user(user_id)
    if not user:
        await message.answer("❌ Пользователь с таким ID не найден.")
        await state.clear()
        return

    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminGrantState.waiting_plan)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Free",  callback_data="grant_plan:free")],
        [InlineKeyboardButton(text="🥈 Basic", callback_data="grant_plan:basic")],
        [InlineKeyboardButton(text="🥇 Pro",   callback_data="grant_plan:pro")],
        [InlineKeyboardButton(text="💎 Ultra", callback_data="grant_plan:ultra")],
    ])

    await message.answer(
        f"✅ Найден: <b>{user.first_name}</b> (@{user.username or '—'})\n\n"
        f"Выбери тариф для выдачи:",
        reply_markup=kb,
        parse_mode="HTML",
    )


@router.callback_query(lambda c: c.data and c.data.startswith("grant_plan:"))
async def cb_grant_plan(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    plan = call.data.split(":")[1]
    data = await state.get_data()
    target_id = data.get("target_user_id")

    if not target_id:
        await call.answer("Ошибка: ID не найден", show_alert=True)
        await state.clear()
        return

    await set_subscription(target_id, plan, days=30)
    await state.clear()

    await call.message.edit_text(
        f"✅ <b>Подписка выдана!</b>\n\n"
        f"Пользователь <code>{target_id}</code>\n"
        f"Тариф: <b>{plan.upper()}</b> на 30 дней",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )

    # Notify user
    try:
        await call.bot.send_message(
            target_id,
            f"🎉 <b>Ваш тариф обновлён!</b>\n\n"
            f"Активирован план: <b>{plan.upper()}</b>\n"
            f"Срок: 30 дней\n\n"
            f"Используй /menu чтобы начать работу!",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await call.answer("✅ Подписка выдана!")
