"""
ExamPaperTestAnswer model - 考卷答题记录（每题一条）
"""
from datetime import datetime
from sqlalchemy import BigInteger, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TestAnswerRecord(Base):
    """考卷答题记录表"""

    __tablename__ = "exam_paper_test_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exam_paper_tests.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    exam_paper_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exam_papers.id"), nullable=False)
    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)
    user_answer: Mapped[str] = mapped_column(String(4), nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(4), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    test = relationship("ExamPaperTest", lazy="selectin")
    user = relationship("User", lazy="selectin")
    exam_paper = relationship("ExamPaper", lazy="selectin")
    question = relationship("Question", lazy="selectin")