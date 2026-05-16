from html import escape
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice

from config import settings
from database.crud import set_subscription, PLAN_STARS
from keyboards import plans_keyboard, back_to_menu_keyboard, buy_plan_keyboard

router = Router()

PLAN_DETAILS = {
    "free": {
        "title": "🆓 Free — Бесплатный",
        "price": "Бесплатно",
        "desc": "Идеально чтобы попробовать бота и оценить возможности нейросетей.",
        "limits": (
            "🟢 ChatGPT: 20/мес · 5/день\n"
            "🟣 Claude: недоступен\n"
            "💾 Сохранение чатов: нет"
        ),
    },
    "basic": {
        "title": "🥈 Basic",
        "price": f"~115 ₽ / мес | {PLAN_STARS['basic']} ⭐",
        "desc": "Для регулярного использования ChatGPT.",
        "limits": (
            "🟢 ChatGPT: 100/мес · 20/день\n"
            "🟣 Claude: недоступен\n"
            "💾 Сохранение чатов: 5"
        ),
    },
    "pro": {
        "title": "🥇 Pro",
        "price": f"~460 ₽ / мес | {PLAN_STARS['pro']} ⭐",
        "desc": "Полный доступ к ChatGPT и Claude. Оптимальный выбор.",
        "limits": (
            "🟢 ChatGPT: 250/мес · 40/день\n"
            "🟣 Claude: 60/мес · 10/день\n"
            "💾 Сохранение чатов: 30"
        ),
    },
    "ultra": {
        "title": "💎 Ultra",
        "price": f"~1150 ₽ / мес | {PLAN_STARS['ultra']} ⭐",
        "desc": "Максимальный тариф для профессионального использования.",
        "limits": (
            "🟢 ChatGPT: 700/мес · 100/день\n"
            "🟣 Claude: 180/мес · 25/день\n"
            "💾 Сохранение чатов: ∞"
        ),
    },
}

PLAN_NAMES = {
    "basic": "Basic",
    "pro": "Pro",
    "ultra": "Ultra",
}


@router.message(Command("plans"))
@router.message(F.text == "💳 Тарифы")
async def cmd_plans(message: Message):
    from texts import get_plans_text
    await message.answer(
        get_plans_text(),
        reply_markup=plans_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(lambda c: c.data == "plans")
async def cb_plans(call: CallbackQuery):
    from texts import get_plans_text
    await call.message.edit_text(
        get_plans_text(),
        reply_markup=plans_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("plan_info:"))
async def cb_plan_info(call: CallbackQuery):
    plan = call.data.split(":")[1]
    info = PLAN_DETAILS.get(plan)
    if not info:
        await call.answer("Тариф не найден", show_alert=True)
        return

    text = (
        f"<b>{info['title']}</b>\n\n"
        f"💰 Цена: <b>{info['price']}</b>\n\n"
        f"📝 {info['desc']}\n\n"
        f"<b>Лимиты:</b>\n{info['limits']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    if plan == "free":
        text += "Бесплатный тариф активен по умолчанию."
        kb = back_to_menu_keyboard()
    else:
        text += f"Нажми кнопку ниже для оплаты через Telegram Stars:"
        kb = buy_plan_keyboard(plan)

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


# ─────────────────────────────────────────────
#  Telegram Stars Payment
# ─────────────────────────────────────────────
@router.callback_query(lambda c: c.data and c.data.startswith("pay_stars:"))
async def cb_pay_stars(call: CallbackQuery, bot: Bot):
    plan = call.data.split(":")[1]
    stars = PLAN_STARS.get(plan)
    name = PLAN_NAMES.get(plan)

    if not stars or not name:
        await call.answer("Тариф не найден", show_alert=True)
        return

    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=f"NEUR AI — {name}",
        description=f"Подписка {name} на 30 дней. Доступ ко всем возможностям тарифа.",
        payload=f"sub_{plan}_30",
        currency="XTR",
        prices=[LabeledPrice(label=f"NEUR AI {name}", amount=stars)],
    )
    await call.answer()


@router.pre_checkout_query()
async def handle_pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message, bot: Bot):
    payload = message.successful_payment.invoice_payload
    parts = payload.split("_")
    if len(parts) != 3 or parts[0] != "sub":
        return

    plan = parts[1]
    days = int(parts[2])

    await set_subscription(message.from_user.id, plan, days)

    await message.answer(
        f"🎉 <b>Оплата прошла успешно!</b>\n\n"
        f"Активирован план: <b>{plan.upper()}</b>\n"
        f"Срок: {days} дней\n\n"
        f"Используй /menu чтобы начать работу!",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )
