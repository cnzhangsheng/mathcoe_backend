"""
Question API router - questions
"""
from fastapi import APIRouter

from app.api.deps import DBSession, CurrentUser
from app.schemas.question import QuestionResponse, QuestionForPractice
from app.services.question_service import QuestionService

router = APIRouter()


@router.get("", response_model=list[QuestionForPractice])
async def get_questions(
    db: DBSession,
    topic_id: int | None = None,
    difficulty: str | None = None,
    year: int | None = None,
    limit: int = 20,
):
    """Get questions with filters"""
    service = QuestionService(db)
    return await service.get_questions(topic_id, difficulty, year, limit)


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: DBSession):
    """Get question by ID"""
    service = QuestionService(db)
    return await service.get_question(question_id)