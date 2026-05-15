import asyncio
import logging
from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import settings
from database.crud import (
    get_all_users, get_stats, set_subscription, get_user,
    ban_user, unban_user, get_all_user_ids,
)
from states import AdminGrantState, AdminBanState, AdminBroadcastState
from keyboards import admin_keyboard, back_to_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_list


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = await get_stats()
    text = (
        f"🔧 <b>Панель администратора</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"💳 Платных подписок: <b>{stats['paid_subs']}</b>\n"
        f"📊 Всего запросов: <b>{stats['total_requests']}</b>\n\n"
        f"🟢 ChatGPT:  {stats['chatgpt_requests']}\n"
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
        f"💳 Платных подписок: <b>{stats['paid_subs']}</b>\n"
        f"📨 Всего запросов: <b>{stats['total_requests']}</b>\n\n"
        f"🟢 ChatGPT:  {stats['chatgpt_requests']}\n"
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
        ban = " 🚫" if u.is_banned else ""
        uname = f"@{u.username}" if u.username else "—"
        lines.append(f"• <b>{u.first_name}</b> {uname} <code>{u.telegram_id}</code>{ban}")
    text = f"👥 <b>Последние пользователи</b> ({len(users)} всего):\n\n" + "\n".join(lines)
    await call.message.edit_text(text, reply_markup=admin_keyboard(), parse_mode="HTML")
    await call.answer()


# ─── Grant ────────────────────────────────────
@router.callback_query(lambda c: c.data == "admin:grant")
async def cb_admin_grant(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminGrantState.waiting_user_id)
    await call.message.answer("🎁 <b>Выдача подписки</b>\n\nВведи Telegram ID:", parse_mode="HTML")
    await call.answer()


@router.message(AdminGrantState.waiting_user_id)
async def admin_grant_user_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введи число.")
        return
    user = await get_user(user_id)
    if not user:
        await message.answer("❌ Пользователь не найден.")
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
        f"✅ Найден: <b>{user.first_name}</b> (@{user.username or '—'})\n\nВыбери тариф:",
        reply_markup=kb, parse_mode="HTML",
    )


@router.callback_query(lambda c: c.data and c.data.startswith("grant_plan:"))
async def cb_grant_plan(call: CallbackQuery, state: FSMContext, bot: Bot):
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
        f"✅ <b>Подписка выдана!</b>\n\nID: <code>{target_id}</code> → <b>{plan.upper()}</b> · 30 дней",
        reply_markup=back_to_menu_keyboard(), parse_mode="HTML",
    )
    try:
        await bot.send_message(
            target_id,
            f"🎉 <b>Тариф обновлён!</b>\n\nПлан: <b>{plan.upper()}</b> · 30 дней\n\n/menu",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await call.answer("✅ Выдано!")


# ─── Ban ──────────────────────────────────────
@router.callback_query(lambda c: c.data == "admin:ban")
async def cb_admin_ban(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminBanState.waiting_user_id)
    await call.message.answer(
        "🚫 <b>Бан / Разбан</b>\n\n"
        "Введи ID (или <code>unban:ID</code> для разбана):",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(AdminBanState.waiting_user_id)
async def admin_ban_user_handler(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    text = message.text.strip()
    unban = text.startswith("unban:")
    try:
        uid = int(text.replace("unban:", "").strip())
    except ValueError:
        await message.answer("❌ Неверный формат.")
        await state.clear()
        return
    await state.clear()
    if unban:
        ok = await unban_user(uid)
        msg = f"✅ <code>{uid}</code> разбанен." if ok else "❌ Не найден."
    else:
        ok = await ban_user(uid)
        msg = f"🚫 <code>{uid}</code> забанен." if ok else "❌ Не найден."
        if ok:
            try:
                await bot.send_message(uid, "⛔ Ваш аккаунт заблокирован.")
            except Exception:
                pass
    await message.answer(msg, reply_markup=admin_keyboard(), parse_mode="HTML")


# ─── Broadcast ────────────────────────────────
@router.callback_query(lambda c: c.data == "admin:broadcast")
async def cb_admin_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminBroadcastState.waiting_message)
    await call.message.answer(
        "📣 <b>Рассылка</b>\n\nНапиши сообщение (поддерживается HTML и фото).\n/cancel — отмена.",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(AdminBroadcastState.waiting_message)
async def admin_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    if message.text and message.text.strip() == "/cancel":
        await state.clear()
        await message.answer("❌ Отменено.", reply_markup=admin_keyboard())
        return
    await state.clear()
    user_ids = await get_all_user_ids()
    status = await message.answer(f"📤 Рассылаю {len(user_ids)} пользователям...")
    sent = failed = 0
    for uid in user_ids:
        try:
            if message.text:
                await bot.send_message(uid, message.text, parse_mode="HTML")
            elif message.photo:
                await bot.send_photo(uid, message.photo[-1].file_id,
                                     caption=message.caption or "", parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await status.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n📤 Отправлено: {sent}\n❌ Ошибок: {failed}",
        reply_markup=admin_keyboard(), parse_mode="HTML",
    )
