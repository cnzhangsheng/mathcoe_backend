"""
Practice API router - practice sessions and records
"""
from fastapi import APIRouter

from app.api.deps import DBSession, CurrentUser
from app.schemas.practice import (
    PracticeStartRequest,
    PracticeStartResponse,
    PracticeSubmitRequest,
    PracticeSubmitResponse,
    PracticeRecordResponse,
)
from app.services.practice_service import PracticeService

router = APIRouter()


@router.post("/start", response_model=PracticeStartResponse)
async def start_practice(request: PracticeStartRequest, db: DBSession, current_user: CurrentUser):
    """Start a practice session"""
    service = PracticeService(db)
    return await service.start_practice(
        user_id=current_user["id"],
        topic_id=request.topic_id,
        mode=request.mode,
        difficulty=request.difficulty,
        year=request.year,
    )


@router.post("/submit", response_model=PracticeSubmitResponse)
async def submit_answer(request: PracticeSubmitRequest, db: DBSession, current_user: CurrentUser):
    """Submit answer"""
    service = PracticeService(db)
    return await service.submit_answer(
        user_id=current_user["id"],
        question_id=request.question_id,
        user_answer=request.user_answer,
        time_spent=request.time_spent,
    )


@router.get("/records", response_model=list[PracticeRecordResponse])
async def get_records(db: DBSession, current_user: CurrentUser, limit: int = 50):
    """Get user practice records"""
    service = PracticeService(db)
    return await service.get_records(current_user["id"], limit)