"""
Question API router - questions
"""
from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DBSession, UserOrNone
from app.models.user import User
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
    level = None
    if user:
        user_result = await db.execute(select(User).where(User.id == user["id"]))
        user_info = user_result.scalar_one_or_none()
        level = user_info.difficulty_level if user_info else None
    service = QuestionService(db)
    return await service.get_questions(topic_id, year, limit, sort_by, level)


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: DBSession):
    """Get question by ID"""
    service = QuestionService(db)
    return await service.get_question(question_id)