from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from keyboards import plans_keyboard, back_to_menu_keyboard
from texts import get_plans_text

router = Router()


@router.message(Command("plans"))
@router.message(F.text == "💳 Тарифы")
async def cmd_plans(message: Message):
    await message.answer(
        get_plans_text(),
        reply_markup=plans_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("buy"))
async def cmd_buy(message: Message):
    text = (
        "💳 <b>Оплата подписки</b>\n\n"
        "Для активации подписки обратись к администратору:\n"
        "👤 @your_admin_username\n\n"
        "После оплаты подписка будет активирована вручную.\n\n"
        "<b>Доступные тарифы:</b>"
    )
    await message.answer(
        text,
        reply_markup=plans_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(lambda c: c.data == "plans")
async def cb_plans(call: CallbackQuery):
    await call.message.edit_text(
        get_plans_text(),
        reply_markup=plans_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("plan_info:"))
async def cb_plan_info(call: CallbackQuery):
    plan = call.data.split(":")[1]

    plan_details = {
        "free": {
            "title": "🆓 Free — Бесплатный",
            "price": "0 ₽ / месяц",
            "desc": "Идеально чтобы попробовать бота и оценить возможности нейросетей.",
            "limits": "• 🟢 ChatGPT: 5 запросов/мес\n• 🔵 DeepSeek: 10 запросов/мес\n• 🟣 Claude: недоступен",
        },
        "basic": {
            "title": "🥈 Basic",
            "price": "~450 ₽ / месяц ($4.99)",
            "desc": "Для регулярного использования ChatGPT и DeepSeek без Claude.",
            "limits": "• 🟢 ChatGPT: 30 запросов/мес\n• 🔵 DeepSeek: 50 запросов/мес\n• 🟣 Claude: недоступен",
        },
        "pro": {
            "title": "🥇 Pro",
            "price": "~900 ₽ / месяц ($9.99)",
            "desc": "Полный доступ ко всем трём нейросетям. Оптимальный выбор для работы.",
            "limits": "• 🟢 ChatGPT: 80 запросов/мес\n• 🟣 Claude: 10 запросов/мес\n• 🔵 DeepSeek: 150 запросов/мес",
        },
        "ultra": {
            "title": "💎 Ultra",
            "price": "~1800 ₽ / месяц ($19.99)",
            "desc": "Максимальный тариф для профессионального использования. DeepSeek — безлимит.",
            "limits": "• 🟢 ChatGPT: 200 запросов/мес\n• 🟣 Claude: 30 запросов/мес\n• 🔵 DeepSeek: ∞ безлимит",
        },
    }

    info = plan_details.get(plan)
    if not info:
        await call.answer("Тариф не найден", show_alert=True)
        return

    text = (
        f"<b>{info['title']}</b>\n\n"
        f"💰 Цена: <b>{info['price']}</b>\n\n"
        f"📝 {info['desc']}\n\n"
        f"<b>Лимиты:</b>\n{info['limits']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Для активации напиши /buy или обратись к @admin"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Купить этот тариф", url="https://t.me/your_admin")],
        [InlineKeyboardButton(text="◀️ Назад к тарифам",  callback_data="plans")],
    ])

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()
