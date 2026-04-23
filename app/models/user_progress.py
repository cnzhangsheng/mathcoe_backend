"""
UserProgress model - 用户专题进度
"""
from sqlalchemy import Integer, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class UserProgress(BaseModel):
    """用户进度表"""

    __tablename__ = "user_progress"
    __table_args__ = (UniqueConstraint("user_id", "topic_id", name="uq_user_topic"),)

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    topic_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("topics.id"), nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    questions_done: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="progress", lazy="selectin")
    topic = relationship("Topic", back_populates="user_progress", lazy="selectin")