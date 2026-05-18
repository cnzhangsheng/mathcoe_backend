"""
Banner model - Banner 配置
"""
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Banner(BaseModel):
    """首页 Banner 表"""

    __tablename__ = "banners"

    image_url: Mapped[str] = mapped_column(String(512), nullable=False)
    link_type: Mapped[str] = mapped_column(String(16), default="content", nullable=False)  # content/external
    link_value: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    position: Mapped[str] = mapped_column(String(32), default="home", nullable=False)  # home/discover/topics/...
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
