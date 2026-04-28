"""
Practice API router - practice sessions and records
"""
from fastapi import APIRouter, Query

from app.api.deps import DBSession, CurrentUser
from app.schemas.practice import (
    PracticeStartRequest,
    PracticeStartResponse,
    PracticeSubmitRequest,
    PracticeSubmitResponse,
    PracticeRecordResponse,
    PracticeRecordsPaginatedResponse,
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


@router.get("/records", response_model=PracticeRecordResponse | PracticeRecordsPaginatedResponse)
async def get_records(
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    detail: bool = Query(default=True),
    topic_id: int | None = Query(default=None),
    time_filter: str | None = Query(default=None),
    result_filter: str | None = Query(default=None),
):
    """Get user practice records with pagination and question details

    Args:
        topic_id: 专题ID筛选
        time_filter: 时间筛选 (day/week/month)
        result_filter: 结果筛选 (correct/wrong)
    """
    service = PracticeService(db)
    if detail:
        return await service.get_records_detail(
            current_user["id"],
            page,
            page_size,
            topic_id=topic_id,
            time_filter=time_filter,
            result_filter=result_filter
        )
    else:
        return await service.get_records(current_user["id"], limit=page_size)


@router.get("/today-stats")
async def get_today_stats(db: DBSession, current_user: CurrentUser):
    """Get user practice statistics for today"""
    service = PracticeService(db)
    return await service.get_today_stats(current_user["id"])