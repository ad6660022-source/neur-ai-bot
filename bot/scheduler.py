import asyncio
import logging
from datetime import datetime, date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from database.crud import (
    get_expiring_subscriptions,
    get_expired_trials,
    mark_expiry_notified,
    get_inactive_users,
)

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="UTC")

PLAN_EMOJI = {"free": "🆓", "basic": "🥈", "pro": "🥇", "ultra": "💎"}


async def notify_expiring_subscriptions(bot: Bot):
    """Daily: warn users whose paid sub expires within 3 days."""
    subs = await get_expiring_subscriptions(within_days=3)
    for sub in subs:
        try:
            days_left = max(0, (sub.expires_at - datetime.utcnow()).days)
            plan_emoji = PLAN_EMOJI.get(sub.plan, "💳")
            await bot.send_message(
                sub.user_id,
                f"⏳ <b>Подписка заканчивается!</b>\n\n"
                f"{plan_emoji} Тариф <b>{sub.plan.upper()}</b> истекает "
                f"через <b>{days_left} дн.</b>\n\n"
                f"Продли сейчас чтобы не потерять доступ к нейросетям:",
                parse_mode="HTML",
                reply_markup=_renew_keyboard(sub.plan),
            )
            await mark_expiry_notified(sub.id)
            logger.info("Expiry notice sent to user %s", sub.user_id)
        except Exception as e:
            logger.warning("Failed to notify user %s: %s", sub.user_id, e)


async def notify_expired_trials(bot: Bot):
    """Hourly: notify users whose 3-day trial just ended."""
    trials = await get_expired_trials()
    for sub in trials:
        try:
            await bot.send_message(
                sub.user_id,
                f"🎁 <b>Твой бесплатный Pro-пробный период завершён!</b>\n\n"
                f"Надеемся, ты успел оценить возможности Claude и ChatGPT.\n\n"
                f"Продолжай с подпиской — выбери подходящий тариф:",
                parse_mode="HTML",
                reply_markup=_plans_keyboard(),
            )
            await mark_expiry_notified(sub.id)
            logger.info("Trial expired notice sent to user %s", sub.user_id)
        except Exception as e:
            logger.warning("Failed to notify trial user %s: %s", sub.user_id, e)


def _renew_keyboard(plan: str):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from database.crud import PLAN_STARS
    stars = PLAN_STARS.get(plan)
    rows = []
    if stars:
        rows.append([InlineKeyboardButton(
            text=f"⭐ Продлить {plan.upper()} за {stars} Stars",
            callback_data=f"pay_stars:{plan}",
        )])
    rows.append([InlineKeyboardButton(text="💳 Все тарифы", callback_data="plans")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _plans_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from database.crud import PLAN_STARS
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🥇 Pro — {PLAN_STARS['pro']} ⭐",   callback_data="pay_stars:pro")],
        [InlineKeyboardButton(text=f"💎 Ultra — {PLAN_STARS['ultra']} ⭐", callback_data="pay_stars:ultra")],
        [InlineKeyboardButton(text="💳 Все тарифы",     callback_data="plans")],
    ])


async def _generate_ai_fact() -> str | None:
    try:
        from openai import AsyncOpenAI
        from config import settings
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        today_str = date.today().strftime("%d %B %Y")
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": (
                    f"Сегодня {today_str}. Напиши короткое (3-4 предложения) интересное сообщение "
                    "об искусственном интеллекте или технологиях. "
                    "Формат: начни с эмодзи, заголовок выдели <b>жирным</b> тегом HTML, "
                    "затем 2-3 предложения текста. В конце добавь: "
                    "'Попробуй NEUR AI — два лучших ИИ в одном боте!'"
                ),
            }],
            max_tokens=250,
            temperature=0.85,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning("Failed to generate AI fact: %s", e)
        return None


async def send_reengagement(bot: Bot):
    """Daily: send AI-generated fact to users inactive for 2+ days."""
    users = await get_inactive_users(days=2)
    if not users:
        logger.info("Re-engagement: no inactive users")
        return

    fact = await _generate_ai_fact()
    if not fact:
        logger.warning("Re-engagement: fact generation failed, skipping")
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Открыть NEUR AI", callback_data="back_to_menu")],
        [InlineKeyboardButton(text="📢 Наш канал @neur_ai_pub", url="https://t.me/neur_ai_pub")],
    ])

    sent = failed = 0
    for user in users[:500]:
        try:
            await bot.send_message(user.telegram_id, fact, parse_mode="HTML", reply_markup=kb)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    logger.info("Re-engagement sent: %d ok, %d failed", sent, failed)


def setup_scheduler(bot: Bot):
    scheduler.add_job(
        notify_expiring_subscriptions,
        trigger="cron",
        hour=10, minute=0,
        args=[bot],
        id="expiry_notify",
        replace_existing=True,
    )
    scheduler.add_job(
        notify_expired_trials,
        trigger="interval",
        hours=1,
        args=[bot],
        id="trial_notify",
        replace_existing=True,
    )
    scheduler.add_job(
        send_reengagement,
        trigger="cron",
        hour=12, minute=0,
        args=[bot],
        id="reengagement",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")
