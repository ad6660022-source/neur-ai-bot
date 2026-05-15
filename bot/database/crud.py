from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Subscription, UsageLog
from database.db import async_session

# ─────────────────────────────────────────────
#  Plan limits
# ─────────────────────────────────────────────
PLAN_LIMITS = {
    "free":  {"chatgpt": 5,   "claude": 0,  "deepseek": 10},
    "basic": {"chatgpt": 30,  "claude": 0,  "deepseek": 50},
    "pro":   {"chatgpt": 80,  "claude": 10, "deepseek": 150},
    "ultra": {"chatgpt": 200, "claude": 30, "deepseek": -1},  # -1 = unlimited
}

PLAN_PRICES = {
    "free":  0.00,
    "basic": 4.99,
    "pro":   9.99,
    "ultra": 19.99,
}

PLAN_EMOJI = {
    "free":  "🆓",
    "basic": "🥈",
    "pro":   "🥇",
    "ultra": "💎",
}


# ─────────────────────────────────────────────
#  User operations
# ─────────────────────────────────────────────
async def get_or_create_user(
    telegram_id: int,
    first_name: str,
    username: Optional[str] = None,
    last_name: Optional[str] = None,
    language_code: Optional[str] = None,
) -> tuple[User, bool]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            return user, False

        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            last_name=last_name,
            language_code=language_code,
        )
        session.add(user)

        # Create free subscription
        sub = Subscription(
            user_id=telegram_id,
            plan="free",
            is_active=True,
        )
        session.add(sub)

        await session.commit()
        await session.refresh(user)
        return user, True


async def get_user(telegram_id: int) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


# ─────────────────────────────────────────────
#  Subscription operations
# ─────────────────────────────────────────────
async def get_active_subscription(telegram_id: int) -> Optional[Subscription]:
    async with async_session() as session:
        result = await session.execute(
            select(Subscription)
            .where(
                Subscription.user_id == telegram_id,
                Subscription.is_active == True,
            )
            .order_by(Subscription.started_at.desc())
        )
        sub = result.scalar_one_or_none()

        if sub:
            # Auto-reset monthly counters
            now = datetime.utcnow()
            if (now - sub.reset_at).days >= 30:
                sub.chatgpt_used = 0
                sub.claude_used = 0
                sub.deepseek_used = 0
                sub.reset_at = now
                await session.commit()
                await session.refresh(sub)

        return sub


async def set_subscription(telegram_id: int, plan: str, days: int = 30) -> Subscription:
    async with async_session() as session:
        # Deactivate existing
        await session.execute(
            update(Subscription)
            .where(Subscription.user_id == telegram_id, Subscription.is_active == True)
            .values(is_active=False)
        )

        sub = Subscription(
            user_id=telegram_id,
            plan=plan,
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=days),
            reset_at=datetime.utcnow(),
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)
        return sub


# ─────────────────────────────────────────────
#  Usage tracking
# ─────────────────────────────────────────────
async def check_and_increment_usage(telegram_id: int, model: str) -> tuple[bool, int, int]:
    """Returns (allowed, used, limit)"""
    sub = await get_active_subscription(telegram_id)
    if not sub:
        return False, 0, 0

    limits = PLAN_LIMITS.get(sub.plan, PLAN_LIMITS["free"])
    limit = limits.get(model, 0)

    field_map = {"chatgpt": "chatgpt_used", "claude": "claude_used", "deepseek": "deepseek_used"}
    field = field_map.get(model)

    used = getattr(sub, field, 0)

    if limit == 0:
        return False, used, limit
    if limit == -1:  # unlimited
        async with async_session() as session:
            await session.execute(
                update(Subscription)
                .where(Subscription.id == sub.id)
                .values(**{field: used + 1})
            )
            await session.commit()
        return True, used + 1, limit

    if used >= limit:
        return False, used, limit

    async with async_session() as session:
        await session.execute(
            update(Subscription)
            .where(Subscription.id == sub.id)
            .values(**{field: used + 1})
        )
        await session.commit()

    return True, used + 1, limit


async def log_usage(telegram_id: int, model: str, prompt_tokens: int = 0,
                    completion_tokens: int = 0, success: bool = True):
    async with async_session() as session:
        log = UsageLog(
            user_id=telegram_id,
            ai_model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            success=success,
        )
        session.add(log)
        await session.commit()


# ─────────────────────────────────────────────
#  Admin
# ─────────────────────────────────────────────
async def get_all_users() -> list[User]:
    async with async_session() as session:
        result = await session.execute(select(User).order_by(User.created_at.desc()))
        return result.scalars().all()


async def get_stats() -> dict:
    from sqlalchemy import func
    async with async_session() as session:
        user_count = (await session.execute(select(func.count(User.id)))).scalar()
        log_count = (await session.execute(select(func.count(UsageLog.id)))).scalar()

        chatgpt_count = (await session.execute(
            select(func.count(UsageLog.id)).where(UsageLog.ai_model == "chatgpt")
        )).scalar()
        claude_count = (await session.execute(
            select(func.count(UsageLog.id)).where(UsageLog.ai_model == "claude")
        )).scalar()
        deepseek_count = (await session.execute(
            select(func.count(UsageLog.id)).where(UsageLog.ai_model == "deepseek")
        )).scalar()

        return {
            "users": user_count,
            "total_requests": log_count,
            "chatgpt_requests": chatgpt_count,
            "claude_requests": claude_count,
            "deepseek_requests": deepseek_count,
        }
