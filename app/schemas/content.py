"""
Content schemas - Pydantic models for content management
"""
from datetime import datetime

from pydantic import BaseModel, field_validator


class ContentBase(BaseModel):
    title: str
    content: str = ""
    slug: str = ""
    status: str = "draft"


class ContentCreate(ContentBase):
    pass


class ContentUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    slug: str | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in ("draft", "published"):
            raise ValueError("status must be draft or published")
        return v


class ContentResponse(ContentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContentDetail(BaseModel):
    """公开接口返回的内容详情"""
    title: str
    content: str
    slug: str
    updated_at: datetime
