"""
Auth schemas
"""
from pydantic import BaseModel


class WeChatLoginRequest(BaseModel):
    code: str  # wx.login() 获取的 code
    nickname: str | None = None  # 用户昵称
    avatar_url: str | None = None  # 用户头像URL


class WeChatLoginResponse(BaseModel):
    token: str
    user_id: int
    openid: str
    nickname: str | None = None
    avatar_url: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"