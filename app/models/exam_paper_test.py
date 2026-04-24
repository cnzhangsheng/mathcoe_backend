"""
ExamPaperTest model - 考卷测试记录
"""
from datetime import datetime
from sqlalchemy import BigInteger, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ExamPaperTest(BaseModel):
    """考卷测试记录表"""

    __tablename__ = "exam_paper_tests"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    exam_paper_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exam_papers.id"), nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 得分（满分100）
    correct_count: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 正确数量
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)  # 总题数
    time_spent: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 用时（秒）
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="in_progress", nullable=False)  # in_progress/completed

    # Relationships
    user = relationship("User", lazy="selectin")
    exam_paper = relationship("ExamPaper", lazy="selectin")