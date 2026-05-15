from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
    usage_logs: Mapped[list["UsageLog"]] = relationship(back_populates="user")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), nullable=False)  # free | basic | pro | ultra
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Monthly usage counters (reset each month)
    chatgpt_used: Mapped[int] = mapped_column(Integer, default=0)
    claude_used: Mapped[int] = mapped_column(Integer, default=0)
    deepseek_used: Mapped[int] = mapped_column(Integer, default=0)
    reset_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="subscriptions")


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    ai_model: Mapped[str] = mapped_column(String(20), nullable=False)  # chatgpt | claude | deepseek
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    success: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="usage_logs")
