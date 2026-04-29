"""
Auth schemas
"""
from pydantic import BaseModel, field_validator


class WeChatLoginRequest(BaseModel):
    code: str  # wx.login() 获取的 code
    nickname: str | None = None  # 用户昵称
    avatar_url: str | None = None  # 用户头像URL
    grade: str = "G1"  # 年级，默认一年级
    difficulty_level: int = 1  # 难度等级 1-6，默认根据年级映射

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        valid_grades = {"G1", "G2", "G3", "G4", "G5", "G6"}
        if v not in valid_grades:
            raise ValueError(f"grade must be one of {valid_grades}, got {v}")
        return v

    @field_validator("difficulty_level")
    @classmethod
    def validate_difficulty(cls, v: int) -> int:
        if v < 1 or v > 6:
            raise ValueError("difficulty_level must be between 1 and 6")
        return v


class WeChatLoginResponse(BaseModel):
    token: str
    user_id: int
    openid: str
    nickname: str | None = None
    avatar_url: str | None = None
    grade: str
    difficulty_level: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"