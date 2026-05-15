from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, update, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Subscription, UsageLog
from database.db import async_session

# ─────────────────────────────────────────────
#  Plan limits (monthly)
# ─────────────────────────────────────────────
PLAN_LIMITS = {
    "free":  {"chatgpt": 5,   "claude": 0,  "deepseek": 10},
    "basic": {"chatgpt": 30,  "claude": 0,  "deepseek": 50},
    "pro":   {"chatgpt": 80,  "claude": 10, "deepseek": 150},
    "ultra": {"chatgpt": 200, "claude": 30, "deepseek": -1},  # -1 = unlimited
}

# Daily limits
DAILY_LIMITS = {
    "free":  {"chatgpt": 3,  "claude": 0,  "deepseek": 5},
    "basic": {"chatgpt": 10, "claude": 0,  "deepseek": 20},
    "pro":   {"chatgpt": 30, "claude": 5,  "deepseek": 60},
    "ultra": {"chatgpt": 80, "claude": 15, "deepseek": -1},
}

PLAN_PRICES = {
    "free":  0.00,
    "basic": 4.99,
    "pro":   9.99,
    "ultra": 19.99,
}

# Telegram Stars prices
PLAN_STARS = {
    "basic": 399,
    "pro":   799,
    "ultra": 1499,
}

PLAN_EMOJI = {
    "free":  "🆓",
    "basic": "🥈",
    "pro":   "🥇",
    "ultra": "💎",
}

# Bonus requests per referral (credited to referrer)
REFERRAL_BONUS = 10


# ─────────────────────────────────────────────
#  User operations
# ─────────────────────────────────────────────
async def get_or_create_user(
    telegram_id: int,
    first_name: str,
    username: Optional[str] = None,
    last_name: Optional[str] = None,
    language_code: Optional[str] = None,
    referred_by: Optional[int] = None,
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
            referral_code=str(telegram_id),
            referred_by=referred_by,
        )
        session.add(user)

        sub = Subscription(
            user_id=telegram_id,
            plan="free",
            is_active=True,
        )
        session.add(sub)

        await session.commit()
        await session.refresh(user)

        # Credit referrer bonus
        if referred_by:
            await _credit_referral_bonus(referred_by, session)

        return user, True


async def _credit_referral_bonus(referrer_id: int, session: AsyncSession):
    await session.execute(
        update(User)
        .where(User.telegram_id == referrer_id)
        .values(bonus_requests=User.bonus_requests + REFERRAL_BONUS)
    )
    await session.commit()


async def get_user(telegram_id: int) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def get_all_users() -> list[User]:
    async with async_session() as session:
        result = await session.execute(select(User).order_by(User.created_at.desc()))
        return result.scalars().all()


async def get_all_user_ids() -> list[int]:
    async with async_session() as session:
        result = await session.execute(
            select(User.telegram_id).where(User.is_banned == False)
        )
        return result.scalars().all()


async def ban_user(telegram_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_banned=True)
        )
        await session.commit()
        return result.rowcount > 0


async def unban_user(telegram_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_banned=False)
        )
        await session.commit()
        return result.rowcount > 0


# ─────────────────────────────────────────────
#  Subscription operations
# ─────────────────────────────────────────────
async def get_active_subscription(telegram_id: int) -> Optional[Subscription]:
    async with async_session() as session:
        now = datetime.utcnow()
        result = await session.execute(
            select(Subscription)
            .where(
                Subscription.user_id == telegram_id,
                Subscription.is_active == True,
                # Bug fix: check expiry (None = free/no expiry)
                or_(Subscription.expires_at.is_(None), Subscription.expires_at > now),
            )
            .order_by(Subscription.started_at.desc())
        )
        sub = result.scalar_one_or_none()

        if sub:
            changed = False
            # Auto-reset monthly counters
            if (now - sub.reset_at).days >= 30:
                sub.chatgpt_used = 0
                sub.claude_used = 0
                sub.deepseek_used = 0
                sub.reset_at = now
                changed = True
            # Auto-reset daily counters
            if (now - sub.daily_reset_at).total_seconds() >= 86400:
                sub.daily_chatgpt_used = 0
                sub.daily_claude_used = 0
                sub.daily_deepseek_used = 0
                sub.daily_reset_at = now
                changed = True
            if changed:
                await session.commit()
                await session.refresh(sub)

        return sub


async def set_subscription(telegram_id: int, plan: str, days: int = 30) -> Subscription:
    async with async_session() as session:
        await session.execute(
            update(Subscription)
            .where(Subscription.user_id == telegram_id, Subscription.is_active == True)
            .values(is_active=False)
        )

        expires = None if plan == "free" else datetime.utcnow() + timedelta(days=days)
        sub = Subscription(
            user_id=telegram_id,
            plan=plan,
            is_active=True,
            expires_at=expires,
            reset_at=datetime.utcnow(),
            daily_reset_at=datetime.utcnow(),
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)
        return sub


# ─────────────────────────────────────────────
#  Usage tracking  (atomic with SELECT FOR UPDATE)
# ─────────────────────────────────────────────
async def check_and_increment_usage(
    telegram_id: int, model: str
) -> tuple[bool, int, int, int, int]:
    """
    Returns (allowed, used_monthly, limit_monthly, used_daily, limit_daily).
    Atomic: uses SELECT FOR UPDATE to prevent race conditions.
    """
    field = f"{model}_used"
    daily_field = f"daily_{model}_used"

    async with async_session() as session:
        async with session.begin():
            now = datetime.utcnow()

            # Lock row to prevent race conditions
            result = await session.execute(
                select(Subscription)
                .where(
                    Subscription.user_id == telegram_id,
                    Subscription.is_active == True,
                    or_(Subscription.expires_at.is_(None), Subscription.expires_at > now),
                )
                .order_by(Subscription.started_at.desc())
                .with_for_update()
            )
            sub = result.scalar_one_or_none()

            if not sub:
                return False, 0, 0, 0, 0

            # Reset monthly if needed
            if (now - sub.reset_at).days >= 30:
                sub.chatgpt_used = 0
                sub.claude_used = 0
                sub.deepseek_used = 0
                sub.reset_at = now

            # Reset daily if needed
            if (now - sub.daily_reset_at).total_seconds() >= 86400:
                sub.daily_chatgpt_used = 0
                sub.daily_claude_used = 0
                sub.daily_deepseek_used = 0
                sub.daily_reset_at = now

            monthly_limit = PLAN_LIMITS.get(sub.plan, PLAN_LIMITS["free"])[model]
            daily_limit = DAILY_LIMITS.get(sub.plan, DAILY_LIMITS["free"])[model]

            used_monthly = getattr(sub, field, 0)
            used_daily = getattr(sub, daily_field, 0)

            # Model not in plan
            if monthly_limit == 0:
                return False, used_monthly, monthly_limit, used_daily, daily_limit

            # Check monthly limit
            if monthly_limit != -1 and used_monthly >= monthly_limit:
                return False, used_monthly, monthly_limit, used_daily, daily_limit

            # Check daily limit
            if daily_limit != -1 and used_daily >= daily_limit:
                return False, used_monthly, monthly_limit, used_daily, daily_limit

            # Check bonus requests (from referrals)
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id).with_for_update()
            )
            user = user_result.scalar_one_or_none()
            if user and user.bonus_requests > 0:
                user.bonus_requests -= 1
                # Don't count against limits, just allow
                setattr(sub, field, used_monthly + 1)
                setattr(sub, daily_field, used_daily + 1)
                return True, used_monthly + 1, monthly_limit, used_daily + 1, daily_limit

            # Increment counters
            setattr(sub, field, used_monthly + 1)
            setattr(sub, daily_field, used_daily + 1)

            return True, used_monthly + 1, monthly_limit, used_daily + 1, daily_limit


async def log_usage(
    telegram_id: int,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    success: bool = True,
):
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
#  Admin statistics
# ─────────────────────────────────────────────
async def get_stats() -> dict:
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

        # Revenue estimate (Stars-based)
        pro_subs = (await session.execute(
            select(func.count(Subscription.id))
            .where(Subscription.is_active == True, Subscription.plan != "free")
        )).scalar()

        return {
            "users": user_count,
            "total_requests": log_count,
            "chatgpt_requests": chatgpt_count,
            "claude_requests": claude_count,
            "deepseek_requests": deepseek_count,
            "paid_subs": pro_subs,
        }
