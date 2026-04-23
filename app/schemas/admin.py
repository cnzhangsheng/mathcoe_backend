"""
Admin schemas
"""
from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    """管理员登录请求"""
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    """管理员登录响应"""
    token: str
    admin_id: int
    username: str
    role: str


class AdminResponse(BaseModel):
    """管理员信息响应"""
    id: int
    username: str
    role: str
    created_at: str | None = None

    class Config:
        from_attributes = True