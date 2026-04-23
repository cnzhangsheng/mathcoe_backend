"""
Favorite and WrongQuestion models
"""
from sqlalchemy import Boolean, Integer, BigInteger, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.models.base import BaseModel, Base


class Favorite(Base):
    """收藏表"""

    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_question_favorite"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="favorites", lazy="selectin")
    question = relationship("Question", back_populates="favorites", lazy="selectin")


class WrongQuestion(Base):
    """错题表"""

    __tablename__ = "wrong_questions"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_question_wrong"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="wrong_questions", lazy="selectin")
    question = relationship("Question", back_populates="wrong_questions", lazy="selectin")