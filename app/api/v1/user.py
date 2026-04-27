"""
User API router - user profile and progress
"""
import logging
from fastapi import APIRouter, HTTPException

from app.api.deps import DBSession, CurrentUser
from app.schemas.user import UserResponse, UserProgressResponse, UserAbilityRadar, UserUpdate, UserStatsResponse
from app.services.user_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user(db: DBSession, current_user: CurrentUser):
    """Get current user info"""
    logger.info(f"获取用户信息: user_id={current_user['id']}")
    service = UserService(db)
    return await service.get_user(current_user["id"])


@router.get("/progress", response_model=list[UserProgressResponse])
async def get_user_progress(db: DBSession, current_user: CurrentUser):
    """Get user progress for all topics"""
    service = UserService(db)
    return await service.get_user_progress(current_user["id"])


@router.get("/ability-radar", response_model=UserAbilityRadar)
async def get_ability_radar(db: DBSession, current_user: CurrentUser):
    """Get user ability radar"""
    service = UserService(db)
    return await service.get_user_ability_radar(current_user["id"])


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(db: DBSession, current_user: CurrentUser):
    """Get user learning statistics"""
    service = UserService(db)
    return await service.get_user_stats(current_user["id"])


@router.patch("/me", response_model=UserResponse)
async def update_user(data: UserUpdate, db: DBSession, current_user: CurrentUser):
    """Update user profile"""
    logger.info(f"更新用户信息: user_id={current_user['id']}, data={data}")
    service = UserService(db)
    result = await service.update_user(current_user["id"], data)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"用户信息更新成功: user_id={current_user['id']}")
    return result