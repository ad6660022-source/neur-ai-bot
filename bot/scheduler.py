import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from database.crud import (
    get_expiring_subscriptions,
    get_expired_trials,
    mark_expiry_notified,
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
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥇 Pro — 799 ⭐",   callback_data="pay_stars:pro")],
        [InlineKeyboardButton(text="💎 Ultra — 1499 ⭐", callback_data="pay_stars:ultra")],
        [InlineKeyboardButton(text="💳 Все тарифы",     callback_data="plans")],
    ])


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
    scheduler.start()
    logger.info("Scheduler started")
