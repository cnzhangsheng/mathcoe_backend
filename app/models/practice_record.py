"""
PracticeRecord model - 答题记录
"""
from sqlalchemy import Boolean, Integer, BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PracticeRecord(BaseModel):
    """答题记录表"""

    __tablename__ = "practice_records"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)
    user_answer: Mapped[str | None] = mapped_column(String(8), nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    time_spent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="practice_records", lazy="selectin")
    question = relationship("Question", back_populates="practice_records", lazy="selectin")