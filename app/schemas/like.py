"""
Like schemas
"""
from datetime import datetime
from pydantic import BaseModel


class LikeRequest(BaseModel):
    question_id: int


class LikeResponse(BaseModel):
    id: int
    question_id: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class LikeStatusResponse(BaseModel):
    is_liked: bool
    like_count: int