"""
Question API router - questions
"""
import logging

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DBSession, CurrentUser, UserOrNone
from app.models.user import User

logger = logging.getLogger(__name__)
from app.schemas.question import QuestionResponse, QuestionForPractice
from app.services.question_service import QuestionService

router = APIRouter()


@router.get("", response_model=list[QuestionForPractice])
async def get_questions(
    db: DBSession,
    user: UserOrNone,
    topic_id: int | None = None,
    year: int | None = None,
    limit: int = 20,
    sort_by: str = "default",
):
    """Get questions with filters"""
    logger.info(f"查询题目列表: topic_id={topic_id}, year={year}, limit={limit}, sort_by={sort_by}")
    level = None
    if user:
        user_result = await db.execute(select(User).where(User.id == user["id"]))
        user_info = user_result.scalar_one_or_none()
        level = user_info.difficulty_level if user_info else None
    service = QuestionService(db)
    return await service.get_questions(topic_id, year, limit, sort_by, level)


@router.get("/recommended", response_model=list[QuestionForPractice])
async def get_recommended_questions(
    db: DBSession,
    user: CurrentUser,
    limit: int = 10,
):
    """获取推荐题目 — 基于用户薄弱专题和难度等级"""
    logger.info(f"获取推荐题目: user_id={user['id']}, limit={limit}")
    user_result = await db.execute(select(User).where(User.id == user["id"]))
    user_info = user_result.scalar_one_or_none()
    level = user_info.difficulty_level if user_info else None
    logger.info(f"用户难度等级: user_id={user['id']}, level={level}")
    service = QuestionService(db)
    result = await service.get_recommended_questions(user["id"], level=level, limit=limit)
    logger.info(f"推荐题目结果: user_id={user['id']}, count={len(result)}")
    return result


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: DBSession):
    """Get question by ID"""
    service = QuestionService(db)
    return await service.get_question(question_id)