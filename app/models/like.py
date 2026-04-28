"""
Like model - 点赞记录
"""
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Like(BaseModel):
    """点赞表"""

    __tablename__ = "likes"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="likes", lazy="selectin")
    question = relationship("Question", back_populates="likes", lazy="selectin")