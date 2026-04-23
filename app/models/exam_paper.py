"""
ExamPaper model - 考卷
"""
from sqlalchemy import BigInteger, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ExamPaper(BaseModel):
    """考卷表"""

    __tablename__ = "exam_papers"

    title: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[str] = mapped_column(String(2), nullable=False)  # A/B/C/D/E/F
    total_questions: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    paper_type: Mapped[str] = mapped_column(String(16), default="daily", nullable=False)  # daily/mock/topic

    # Relationships
    questions = relationship("ExamPaperQuestion", back_populates="exam_paper", lazy="selectin", order_by="ExamPaperQuestion.sort")


class ExamPaperQuestion(BaseModel):
    """考卷题目关联表"""

    __tablename__ = "exam_paper_questions"

    exam_paper_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exam_papers.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)
    sort: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 题目顺序 1~10

    # Relationships
    exam_paper = relationship("ExamPaper", back_populates="questions", lazy="selectin")
    question = relationship("Question", lazy="selectin")