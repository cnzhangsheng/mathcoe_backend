"""
Feedback model - 用户意见反馈
"""
from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Feedback(BaseModel):
    """用户反馈表"""

    __tablename__ = "feedbacks"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    contact: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    admin_reply: Mapped[str | None] = mapped_column(Text, nullable=True)