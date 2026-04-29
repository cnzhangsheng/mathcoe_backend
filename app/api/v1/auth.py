"""
Auth API router - WeChat login
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBSession
from app.schemas.auth import WeChatLoginRequest, WeChatLoginResponse, TokenResponse
from app.services.auth_service import AuthService
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)
router = APIRouter()
auth_service = AuthService()


@router.post("/wx-login", response_model=WeChatLoginResponse)
async def wechat_login(request: WeChatLoginRequest, db: DBSession):
    """WeChat mini program login"""
    logger.info(f"微信登录请求: code={request.code}, nickname={request.nickname}, grade={request.grade}")

    # 获取 openid
    wx_data = await auth_service.get_wechat_openid(request.code)
    openid = wx_data["openid"]
    logger.info(f"获取openid成功: openid={openid}")

    # 创建或获取用户，并更新用户信息
    user_repo = UserRepository(db)
    user = await user_repo.create_or_get_by_openid(
        openid,
        nickname=request.nickname,
        avatar_url=request.avatar_url,
        grade=request.grade,
        difficulty_level=request.difficulty_level
    )
    logger.info(f"用户登录成功: user_id={user.id}, openid={openid}, difficulty_level={request.difficulty_level}")

    # 生成 JWT token
    token = auth_service.create_token(user.id, openid)

    return WeChatLoginResponse(
        token=token,
        user_id=user.id,
        openid=openid,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        grade=user.grade,
        difficulty_level=user.difficulty_level
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token():
    """Refresh JWT token"""
    # TODO: 实现 token 刷新逻辑
    return TokenResponse(access_token="refreshed_token")