"""
Favorites API router - favorites and wrong questions
"""
import logging
from fastapi import APIRouter, Query

from app.api.deps import DBSession, CurrentUser
from app.schemas.practice import FavoriteRequest, WrongQuestionRequest, FavoriteResponse, WrongQuestionResponse, WrongQuestionDetailResponse, FavoriteDetailResponse, WrongQuestionsPaginatedResponse, FavoritesPaginatedResponse
from app.services.practice_service import PracticeService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=FavoritesPaginatedResponse)
async def get_favorites(
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=200),
    topic_id: int | None = Query(default=None),
):
    """Get user favorites with full question info (paginated)"""
    logger.info(f"获取收藏列表: user_id={current_user['id']}, page={page}, page_size={page_size}, topic_id={topic_id}")
    service = PracticeService(db)
    return await service.get_favorites_paginated(current_user["id"], page, page_size, topic_id=topic_id)


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


@router.get("/wrong", response_model=WrongQuestionsPaginatedResponse)
async def get_wrong_questions(
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=200),
    topic_id: int | None = Query(default=None),
):
    """Get user wrong questions with full question info (paginated)"""
    logger.info(f"获取错题列表: user_id={current_user['id']}, page={page}, page_size={page_size}, topic_id={topic_id}")
    service = PracticeService(db)
    return await service.get_wrong_questions_paginated(current_user["id"], page, page_size, topic_id=topic_id)


@router.post("/wrong", response_model=WrongQuestionResponse)
async def add_wrong_question(request: WrongQuestionRequest, db: DBSession, current_user: CurrentUser):
    """Add question to wrong questions list"""
    logger.info(f"添加错题: user_id={current_user['id']}, question_id={request.question_id}, user_answer={request.user_answer}")
    service = PracticeService(db)
    wrong_question = await service.add_wrong_question(current_user["id"], request.question_id, request.user_answer)
    logger.info(f"错题添加成功: wrong_question_id={wrong_question.id}")
    return wrong_question


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