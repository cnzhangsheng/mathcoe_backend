"""
User schemas
"""
from datetime import date, datetime
from pydantic import BaseModel


class UserBase(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None


class UserCreate(UserBase):
    openid: str


class UserUpdate(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    streak_days: int | None = None
    last_active_date: date | None = None


class UserResponse(BaseModel):
    id: int
    openid: str
    nickname: str | None
    avatar_url: str | None
    streak_days: int
    last_active_date: date | None
    last_login_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class UserProgressResponse(BaseModel):
    topic_id: int
    topic_title: str | None = None
    progress: int
    success_rate: int
    questions_done: int

    class Config:
        from_attributes = True


class UserAbilityRadar(BaseModel):
    abilities: list[dict[str, int | str]]
    overall_rank: int | None = None