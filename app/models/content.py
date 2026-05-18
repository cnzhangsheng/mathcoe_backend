"""
Content model - 内容管理
"""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Content(BaseModel):
    """内容表"""

    __tablename__ = "contents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")  # 富文本 HTML
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)  # draft/published
