"""
User model - 微信小程序用户
"""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class User(BaseModel):
    """用户表"""

    __tablename__ = "users"

    openid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 最后登录时间
    grade: Mapped[str] = mapped_column(String(2), default="G1", nullable=False)  # 年级 G1-G6
    daily_goal: Mapped[int] = mapped_column(Integer, default=10, nullable=False)  # 每日目标题数

    # Relationships
    progress = relationship("UserProgress", back_populates="user", lazy="selectin")
    practice_records = relationship("PracticeRecord", back_populates="user", lazy="selectin")
    favorites = relationship("Favorite", back_populates="user", lazy="selectin")
    wrong_questions = relationship("WrongQuestion", back_populates="user", lazy="selectin")
    likes = relationship("Like", back_populates="user", lazy="selectin")