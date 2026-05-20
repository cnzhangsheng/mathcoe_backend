"""
User schemas
"""
from datetime import date, datetime
from pydantic import BaseModel, field_validator


class UserBase(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    grade: str = "G1"
    difficulty_level: int = 1

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
    daily_goal: int | None = None
    difficulty_level: int | None = None

    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_grades = {'G1', 'G2', 'G3', 'G4', 'G5', 'G6'}
        if v not in valid_grades:
            raise ValueError(f'grade must be one of {valid_grades}')
        return v

    @field_validator('daily_goal')
    @classmethod
    def validate_daily_goal(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v <= 0:
            raise ValueError('daily_goal must be positive')
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
    daily_goal: int
    difficulty_level: int
    user_tier: str = "free"
    tier_expires_at: datetime | None = None

    class Config:
        from_attributes = True


class UserTierUpdate(BaseModel):
    """Admin-only schema for updating user tier"""
    user_tier: str = "free"
    tier_expires_at: datetime | None = None

    @field_validator('user_tier')
    @classmethod
    def validate_tier(cls, v: str) -> str:
        valid_tiers = {'free', 'pro'}
        if v not in valid_tiers:
            raise ValueError(f'user_tier must be one of {valid_tiers}')
        return v


class UserInsightResponse(BaseModel):
    """AI learning insight data"""
    weakest_topic_id: int | None = None
    weakest_topic_title: str = "未知专题"
    progress_gain: int = 0
    analysis_base: int = 0


class UserAbilityRadar(BaseModel):
    abilities: list[dict[str, int | str]]
    overall_rank: int | None = None


class UserStatsResponse(BaseModel):
    """User learning statistics (weekly + monthly)"""
    # 本周统计
    week_start: str
    week_end: str
    total_questions: int
    correct_count: int
    wrong_count: int
    correct_rate: int
    total_wrong_count: int
    favorite_count: int
    # 本月统计
    month_start: str | None = None
    month_end: str | None = None
    month_total_questions: int = 0
    month_correct_count: int = 0
    month_wrong_count: int = 0
    month_correct_rate: int = 0