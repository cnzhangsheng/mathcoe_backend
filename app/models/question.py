"""
Question model - 题目
"""
from typing import Any

from sqlalchemy import Integer, BigInteger, String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Question(BaseModel):
    """题目表"""

    __tablename__ = "questions"

    topic_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("topics.id"), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    question_type: Mapped[str] = mapped_column(String(16), default="single", nullable=False)
    options: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    answer: Mapped[str] = mapped_column(String(32), nullable=False)
    explanation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(16), nullable=True)
    level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 级别 1-6
    source_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    topic = relationship("Topic", back_populates="questions", lazy="selectin")
    practice_records = relationship("PracticeRecord", back_populates="question", lazy="selectin")
    favorites = relationship("Favorite", back_populates="question", lazy="selectin")
    wrong_questions = relationship("WrongQuestion", back_populates="question", lazy="selectin")