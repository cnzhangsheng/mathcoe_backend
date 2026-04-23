"""
Base model with common fields
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.utils.id_generator import short_id


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""

    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class IDMixin:
    """Mixin for short ID (11-12位纯数字)"""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)


class BaseModel(Base, IDMixin, TimestampMixin):
    """Base model with short ID and timestamps"""

    __abstract__ = True

    def __init__(self, **kwargs):
        # 如果没有提供 id，自动生成短ID
        if "id" not in kwargs:
            kwargs["id"] = short_id()
        super().__init__(**kwargs)