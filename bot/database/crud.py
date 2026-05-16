import json
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, update, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Subscription, UsageLog, SavedChat
from database.db import async_session

# ─────────────────────────────────────────────
#  Plan limits
# ─────────────────────────────────────────────
PLAN_LIMITS = {
    "free":  {"chatgpt": 50,  "claude": 0,   "deepseek": 50},
    "basic": {"chatgpt": 100, "claude": 0,   "deepseek": 100},
    "pro":   {"chatgpt": 200, "claude": 30,  "deepseek": 150},
    "ultra": {"chatgpt": 500, "claude": 100, "deepseek": -1},
}

DAILY_LIMITS = {
    "free":  {"chatgpt": 10, "claude": 0,  "deepseek": 10},
    "basic": {"chatgpt": 20, "claude": 0,  "deepseek": 20},
    "pro":   {"chatgpt": 30, "claude": 5,  "deepseek": 60},
    "ultra": {"chatgpt": 80, "claude": 20, "deepseek": -1},
}

PLAN_PRICES = {
    "free":  0.00,
    "basic": 4.99,
    "pro":   9.99,
    "ultra": 19.99,
}

PLAN_STARS = {
    "basic": 99,
    "pro":   499,
    "ultra": 1499,
}

PLAN_EMOJI = {
    "free":  "🆓",
    "basic": "🥈",
    "pro":   "🥇",
    "ultra": "💎",
}

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

        # Base free subscription (never expires — fallback after trial)
        sub = Subscription(user_id=telegram_id, plan="free", is_active=True)
        session.add(sub)

        await session.commit()
        await session.refresh(user)

        if referred_by:
            await session.execute(
                update(User)
                .where(User.telegram_id == referred_by)
                .values(bonus_requests=User.bonus_requests + REFERRAL_BONUS)
            )
            await session.commit()

        return user, True


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
        r = await session.execute(
            update(User).where(User.telegram_id == telegram_id).values(is_banned=True)
        )
        await session.commit()
        return r.rowcount > 0


async def unban_user(telegram_id: int) -> bool:
    async with async_session() as session:
        r = await session.execute(
            update(User).where(User.telegram_id == telegram_id).values(is_banned=False)
        )
        await session.commit()
        return r.rowcount > 0


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
                or_(Subscription.expires_at.is_(None), Subscription.expires_at > now),
            )
            .order_by(Subscription.started_at.desc())
            .limit(1)
        )
        sub = result.scalars().first()

        if sub:
            changed = False
            if (now - sub.reset_at).days >= 30:
                sub.chatgpt_used = 0
                sub.claude_used = 0
                sub.deepseek_used = 0
                sub.image_used = 0
                sub.reset_at = now
                changed = True
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


async def grant_trial(telegram_id: int) -> Subscription:
    """
    Give 3-day Pro trial WITHOUT deactivating the free subscription.
    When trial expires, get_active_subscription falls back to free automatically.
    """
    async with async_session() as session:
        trial = Subscription(
            user_id=telegram_id,
            plan="pro",
            is_active=True,
            is_trial=True,
            expires_at=datetime.utcnow() + timedelta(days=3),
            reset_at=datetime.utcnow(),
            daily_reset_at=datetime.utcnow(),
        )
        session.add(trial)
        await session.commit()
        await session.refresh(trial)
        return trial


# ─────────────────────────────────────────────
#  Usage tracking  (atomic SELECT FOR UPDATE)
# ─────────────────────────────────────────────
async def check_and_increment_usage(
    telegram_id: int, model: str
) -> tuple[bool, int, int, int, int]:
    """Returns (allowed, used_monthly, limit_monthly, used_daily, limit_daily)."""
    field = f"{model}_used"
    daily_field = f"daily_{model}_used"

    async with async_session() as session:
        async with session.begin():
            now = datetime.utcnow()
            result = await session.execute(
                select(Subscription)
                .where(
                    Subscription.user_id == telegram_id,
                    Subscription.is_active == True,
                    or_(Subscription.expires_at.is_(None), Subscription.expires_at > now),
                )
                .order_by(Subscription.started_at.desc())
                .limit(1)
                .with_for_update()
            )
            sub = result.scalars().first()
            if not sub:
                return False, 0, 0, 0, 0

            if (now - sub.reset_at).days >= 30:
                sub.chatgpt_used = 0
                sub.claude_used = 0
                sub.deepseek_used = 0
                sub.reset_at = now

            if (now - sub.daily_reset_at).total_seconds() >= 86400:
                sub.daily_chatgpt_used = 0
                sub.daily_claude_used = 0
                sub.daily_deepseek_used = 0
                sub.daily_reset_at = now

            monthly_limit = PLAN_LIMITS.get(sub.plan, PLAN_LIMITS["free"])[model]
            daily_limit = DAILY_LIMITS.get(sub.plan, DAILY_LIMITS["free"])[model]
            used_monthly = getattr(sub, field, 0)
            used_daily = getattr(sub, daily_field, 0)

            if monthly_limit == 0:
                return False, used_monthly, monthly_limit, used_daily, daily_limit
            if monthly_limit != -1 and used_monthly >= monthly_limit:
                return False, used_monthly, monthly_limit, used_daily, daily_limit
            if daily_limit != -1 and used_daily >= daily_limit:
                return False, used_monthly, monthly_limit, used_daily, daily_limit

            # Consume bonus requests first (from referrals)
            user_res = await session.execute(
                select(User).where(User.telegram_id == telegram_id).with_for_update()
            )
            user = user_res.scalar_one_or_none()
            if user and user.bonus_requests > 0:
                user.bonus_requests -= 1

            setattr(sub, field, used_monthly + 1)
            setattr(sub, daily_field, used_daily + 1)
            return True, used_monthly + 1, monthly_limit, used_daily + 1, daily_limit


async def check_and_increment_image(telegram_id: int) -> tuple[bool, int, int, str]:
    """Returns (allowed, used, limit, period_label)."""
    from services.image_service import IMAGE_DAILY_LIMITS, IMAGE_MONTHLY_LIMITS
    async with async_session() as session:
        async with session.begin():
            now = datetime.utcnow()
            result = await session.execute(
                select(Subscription)
                .where(
                    Subscription.user_id == telegram_id,
                    Subscription.is_active == True,
                    or_(Subscription.expires_at.is_(None), Subscription.expires_at > now),
                )
                .order_by(Subscription.started_at.desc())
                .limit(1)
                .with_for_update()
            )
            sub = result.scalars().first()
            if not sub:
                return False, 0, 0, "день"

            if (now - sub.reset_at).days >= 30:
                sub.chatgpt_used = 0
                sub.claude_used = 0
                sub.deepseek_used = 0
                sub.image_used = 0
                sub.reset_at = now

            if (now - sub.daily_reset_at).total_seconds() >= 86400:
                sub.daily_chatgpt_used = 0
                sub.daily_claude_used = 0
                sub.daily_deepseek_used = 0
                sub.daily_image_used = 0
                sub.daily_reset_at = now

            if sub.plan == "free":
                limit = IMAGE_MONTHLY_LIMITS.get("free", 0)
                used = getattr(sub, "image_used", 0)
                if limit == 0 or used >= limit:
                    return False, used, limit, "месяц"
                sub.image_used = used + 1
                return True, used + 1, limit, "месяц"
            else:
                limit = IMAGE_DAILY_LIMITS.get(sub.plan, 0)
                used = getattr(sub, "daily_image_used", 0)
                if limit == 0 or used >= limit:
                    return False, used, limit, "день"
                sub.daily_image_used = used + 1
                return True, used + 1, limit, "день"


async def log_usage(
    telegram_id: int, model: str,
    prompt_tokens: int = 0, completion_tokens: int = 0, success: bool = True,
):
    async with async_session() as session:
        session.add(UsageLog(
            user_id=telegram_id,
            ai_model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            success=success,
        ))
        await session.commit()


# ─────────────────────────────────────────────
#  Saved chats
# ─────────────────────────────────────────────
async def save_chat(
    user_id: int, name: str, model: str, mode: str, history: list[dict]
) -> SavedChat:
    async with async_session() as session:
        chat = SavedChat(
            user_id=user_id,
            name=name,
            model=model,
            mode=mode,
            history=json.dumps(history, ensure_ascii=False),
        )
        session.add(chat)
        await session.commit()
        await session.refresh(chat)
        return chat


async def get_saved_chats(user_id: int) -> list[SavedChat]:
    async with async_session() as session:
        result = await session.execute(
            select(SavedChat)
            .where(SavedChat.user_id == user_id)
            .order_by(SavedChat.created_at.desc())
        )
        return result.scalars().all()


async def get_saved_chat(chat_id: int, user_id: int) -> Optional[SavedChat]:
    async with async_session() as session:
        result = await session.execute(
            select(SavedChat).where(
                SavedChat.id == chat_id,
                SavedChat.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()


async def delete_saved_chat(chat_id: int, user_id: int) -> bool:
    async with async_session() as session:
        chat = (await session.execute(
            select(SavedChat).where(SavedChat.id == chat_id, SavedChat.user_id == user_id)
        )).scalar_one_or_none()
        if not chat:
            return False
        await session.delete(chat)
        await session.commit()
        return True


async def get_saved_chat_count(user_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(SavedChat.id)).where(SavedChat.user_id == user_id)
        )
        return result.scalar() or 0


# ─────────────────────────────────────────────
#  Scheduler helpers
# ─────────────────────────────────────────────
async def get_expiring_subscriptions(within_days: int = 3) -> list[Subscription]:
    """Find active paid subs expiring within `within_days` days, not yet notified."""
    async with async_session() as session:
        now = datetime.utcnow()
        deadline = now + timedelta(days=within_days)
        result = await session.execute(
            select(Subscription).where(
                Subscription.is_active == True,
                Subscription.plan != "free",
                Subscription.expires_at.isnot(None),
                Subscription.expires_at > now,
                Subscription.expires_at <= deadline,
                Subscription.expiry_notified == False,
            )
        )
        return result.scalars().all()


async def mark_expiry_notified(sub_id: int):
    async with async_session() as session:
        await session.execute(
            update(Subscription).where(Subscription.id == sub_id).values(expiry_notified=True)
        )
        await session.commit()


async def get_expired_trials() -> list[Subscription]:
    """Find trials that just expired (within last 2 hours), not yet notified."""
    async with async_session() as session:
        now = datetime.utcnow()
        result = await session.execute(
            select(Subscription).where(
                Subscription.is_trial == True,
                Subscription.is_active == True,
                Subscription.expires_at < now,
                Subscription.expires_at > now - timedelta(hours=2),
                Subscription.expiry_notified == False,
            )
        )
        return result.scalars().all()


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
        paid_subs = (await session.execute(
            select(func.count(Subscription.id))
            .where(Subscription.is_active == True, Subscription.plan != "free")
        )).scalar()
        return {
            "users": user_count,
            "total_requests": log_count,
            "chatgpt_requests": chatgpt_count,
            "claude_requests": claude_count,
            "deepseek_requests": deepseek_count,
            "paid_subs": paid_subs,
        }
