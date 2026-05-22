"""
Feedback schemas - 意见反馈
"""
from datetime import datetime

from pydantic import BaseModel, field_validator


class FeedbackCreate(BaseModel):
    content: str
    contact: str | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("反馈内容不能为空")
        return v.strip()


class FeedbackUpdate(BaseModel):
    status: str | None = None
    admin_reply: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in ("pending", "processing", "resolved"):
            raise ValueError("status must be pending, processing, or resolved")
        return v


class FeedbackResponse(BaseModel):
    id: int
    content: str
    contact: str | None = None
    status: str
    admin_reply: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FeedbackAdminResponse(FeedbackResponse):
    """管理员端返回，包含 user_id"""
    user_id: int