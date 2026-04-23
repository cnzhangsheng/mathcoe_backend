"""
Topic model - 专题训练分类
"""
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Topic(BaseModel):
    """专题表"""

    __tablename__ = "topics"

    title: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(16), nullable=True)  # L1-L2, L2-L3
    icon: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 图标标识
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)  # 颜色主题
    is_high_freq: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    questions = relationship("Question", back_populates="topic", lazy="selectin")
    user_progress = relationship("UserProgress", back_populates="topic", lazy="selectin")