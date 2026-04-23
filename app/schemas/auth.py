"""
Auth schemas
"""
from pydantic import BaseModel, field_validator


class WeChatLoginRequest(BaseModel):
    code: str  # wx.login() 获取的 code
    nickname: str | None = None  # 用户昵称
    avatar_url: str | None = None  # 用户头像URL
    grade: str = "G1"  # 年级，默认一年级

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        valid_grades = {"G1", "G2", "G3", "G4", "G5", "G6"}
        if v not in valid_grades:
            raise ValueError(f"grade must be one of {valid_grades}, got {v}")
        return v


class WeChatLoginResponse(BaseModel):
    token: str
    user_id: int
    openid: str
    nickname: str | None = None
    avatar_url: str | None = None
    grade: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"