"""
Favorites API router - favorites and wrong questions
"""
import logging
from fastapi import APIRouter

from app.api.deps import DBSession, CurrentUser
from app.schemas.practice import FavoriteRequest, FavoriteResponse, WrongQuestionResponse, WrongQuestionDetailResponse, FavoriteDetailResponse
from app.services.practice_service import PracticeService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=list[FavoriteDetailResponse])
async def get_favorites(db: DBSession, current_user: CurrentUser):
    """Get user favorites with full question info"""
    logger.info(f"获取收藏列表: user_id={current_user['id']}")
    service = PracticeService(db)
    favorites = await service.get_favorites(current_user["id"])
    logger.info(f"收藏列表返回: count={len(favorites)}")
    return favorites


@router.post("", response_model=FavoriteResponse)
async def add_favorite(request: FavoriteRequest, db: DBSession, current_user: CurrentUser):
    """Add question to favorites"""
    logger.info(f"添加收藏: user_id={current_user['id']}, question_id={request.question_id}")
    service = PracticeService(db)
    favorite = await service.add_favorite(current_user["id"], request.question_id)
    logger.info(f"收藏添加成功: favorite_id={favorite.id}")
    return favorite


@router.delete("")
async def remove_favorite(request: FavoriteRequest, db: DBSession, current_user: CurrentUser):
    """Remove question from favorites"""
    logger.info(f"取消收藏: user_id={current_user['id']}, question_id={request.question_id}")
    service = PracticeService(db)
    success = await service.remove_favorite(current_user["id"], request.question_id)
    logger.info(f"取消收藏结果: success={success}")
    return {"success": success}


@router.get("/wrong", response_model=list[WrongQuestionDetailResponse])
async def get_wrong_questions(db: DBSession, current_user: CurrentUser):
    """Get user wrong questions with full question info"""
    logger.info(f"获取错题列表: user_id={current_user['id']}")
    service = PracticeService(db)
    wrong_questions = await service.get_wrong_questions(current_user["id"])
    logger.info(f"错题列表返回: count={len(wrong_questions)}")
    return wrong_questions


@router.put("/wrong/{question_id}/master")
async def mark_wrong_mastered(question_id: int, db: DBSession, current_user: CurrentUser):
    """Mark a wrong question as mastered"""
    logger.info(f"标记错题已掌握: user_id={current_user['id']}, question_id={question_id}")
    service = PracticeService(db)
    success = await service.mark_wrong_mastered(current_user["id"], question_id)
    logger.info(f"标记掌握结果: success={success}")
    return {"success": success}


@router.delete("/wrong/{question_id}")
async def remove_wrong_question(question_id: int, db: DBSession, current_user: CurrentUser):
    """Remove a wrong question from the list"""
    logger.info(f"删除错题: user_id={current_user['id']}, question_id={question_id}")
    service = PracticeService(db)
    success = await service.remove_wrong_question(current_user["id"], question_id)
    logger.info(f"删除错题结果: success={success}")
    return {"success": success}