"""
Auth API router - WeChat login
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBSession
from app.schemas.auth import WeChatLoginRequest, WeChatLoginResponse, TokenResponse
from app.services.auth_service import AuthService
from app.repositories.user_repo import UserRepository

router = APIRouter()
auth_service = AuthService()


@router.post("/wx-login", response_model=WeChatLoginResponse)
async def wechat_login(request: WeChatLoginRequest, db: DBSession):
    """WeChat mini program login"""
    # 获取 openid
    wx_data = await auth_service.get_wechat_openid(request.code)
    openid = wx_data["openid"]

    # 创建或获取用户，并更新用户信息
    user_repo = UserRepository(db)
    user = await user_repo.create_or_get_by_openid(
        openid,
        nickname=request.nickname,
        avatar_url=request.avatar_url
    )

    # 生成 JWT token
    token = auth_service.create_token(user.id, openid)

    return WeChatLoginResponse(
        token=token,
        user_id=user.id,
        openid=openid,
        nickname=user.nickname,
        avatar_url=user.avatar_url
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token():
    """Refresh JWT token"""
    # TODO: 实现 token 刷新逻辑
    return TokenResponse(access_token="refreshed_token")