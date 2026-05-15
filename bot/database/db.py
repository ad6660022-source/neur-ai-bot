import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# (table, column, sql_definition)
_MIGRATIONS = [
    # Referral system
    ("users", "referral_code",  "VARCHAR(32)"),
    ("users", "referred_by",    "BIGINT"),
    ("users", "bonus_requests", "INTEGER NOT NULL DEFAULT 0"),
    # Daily limits
    ("subscriptions", "daily_chatgpt_used",  "INTEGER NOT NULL DEFAULT 0"),
    ("subscriptions", "daily_claude_used",   "INTEGER NOT NULL DEFAULT 0"),
    ("subscriptions", "daily_deepseek_used", "INTEGER NOT NULL DEFAULT 0"),
    ("subscriptions", "daily_reset_at",      "TIMESTAMP DEFAULT NOW()"),
    # Trial & notification flags
    ("subscriptions", "is_trial",          "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("subscriptions", "expiry_notified",   "BOOLEAN NOT NULL DEFAULT FALSE"),
    # Saved chats mode column (table created by create_all, mode column added just in case)
    ("saved_chats", "mode", "VARCHAR(20) NOT NULL DEFAULT 'default'"),
    # Image generation daily counter
    ("subscriptions", "daily_image_used", "INTEGER NOT NULL DEFAULT 0"),
]


async def _run_migrations(conn):
    is_sqlite = "sqlite" in settings.DATABASE_URL

    for table, column, definition in _MIGRATIONS:
        try:
            if is_sqlite:
                await conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                )
            else:
                await conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {definition}")
                )
            logger.info("Migration applied: %s.%s", table, column)
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" in msg or "already exists" in msg:
                pass  # already exists, fine
            else:
                logger.warning("Migration skipped %s.%s: %s", table, column, e)


async def init_db():
    from database.models import User, Subscription, UsageLog, SavedChat  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_migrations(conn)
