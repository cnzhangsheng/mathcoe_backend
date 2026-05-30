"""
UserDownloadRecord model - 用户下载记录
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class UserDownloadRecord(BaseModel):
    """用户下载记录表"""

    __tablename__ = "user_download_records"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    exam_paper_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    exam_paper_title: Mapped[str] = mapped_column(String(128), nullable=False)
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )