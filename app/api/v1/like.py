"""
Like API router - likes for questions
"""
import logging
from fastapi import APIRouter

from app.api.deps import DBSession, CurrentUser
from app.schemas.like import LikeRequest, LikeResponse, LikeStatusResponse
from app.services.like_service import LikeService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{question_id}/status", response_model=LikeStatusResponse)
async def get_like_status(question_id: int, db: DBSession, current_user: CurrentUser):
    """Get like status and count for a question"""
    logger.info(f"获取点赞状态: user_id={current_user['id']}, question_id={question_id}")
    service = LikeService(db)
    is_liked = await service.is_liked(current_user["id"], question_id)
    like_count = await service.get_like_count(question_id)
    return LikeStatusResponse(is_liked=is_liked, like_count=like_count)


@router.post("", response_model=LikeResponse)
async def add_like(request: LikeRequest, db: DBSession, current_user: CurrentUser):
    """Add like to question"""
    logger.info(f"添加点赞: user_id={current_user['id']}, question_id={request.question_id}")
    service = LikeService(db)
    like = await service.add_like(current_user["id"], request.question_id)
    return like


@router.delete("")
async def remove_like(request: LikeRequest, db: DBSession, current_user: CurrentUser):
    """Remove like from question"""
    logger.info(f"取消点赞: user_id={current_user['id']}, question_id={request.question_id}")
    service = LikeService(db)
    success = await service.remove_like(current_user["id"], request.question_id)
    return {"success": success}