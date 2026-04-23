"""
Topic schemas
"""
from datetime import datetime
from pydantic import BaseModel


class TopicBase(BaseModel):
    title: str
    description: str | None = None
    difficulty: str | None = None
    icon: str | None = None
    color: str | None = None
    is_high_freq: bool = False


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    difficulty: str | None = None
    icon: str | None = None
    color: str | None = None
    is_high_freq: bool | None = None


class TopicResponse(BaseModel):
    id: int
    title: str
    description: str | None
    difficulty: str | None
    icon: str | None
    color: str | None
    is_high_freq: bool
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class TopicWithProgress(TopicResponse):
    progress: int = 0
    success_rate: int = 0
    questions_done: int = 0