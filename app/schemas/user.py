"""
User schemas
"""
from datetime import date, datetime
from pydantic import BaseModel, field_validator


class UserBase(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    grade: str = "G1"

    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v: str) -> str:
        valid_grades = {'G1', 'G2', 'G3', 'G4', 'G5', 'G6'}
        if v not in valid_grades:
            raise ValueError(f'grade must be one of {valid_grades}')
        return v


class UserCreate(UserBase):
    openid: str


class UserUpdate(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    streak_days: int | None = None
    last_active_date: date | None = None
    grade: str | None = None

    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_grades = {'G1', 'G2', 'G3', 'G4', 'G5', 'G6'}
        if v not in valid_grades:
            raise ValueError(f'grade must be one of {valid_grades}')
        return v


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
    grade: str

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