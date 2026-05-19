"""
Practice API router - practice sessions and records
"""
import logging

from fastapi import APIRouter, Query
from sqlalchemy import select, func, cast, Integer

from app.api.deps import DBSession, CurrentUser

logger = logging.getLogger(__name__)
from app.models.user import User
from app.models.question import Question
from app.models.topic import Topic
from app.models.practice_record import PracticeRecord
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
    # 获取用户难度等级
    user_result = await db.execute(select(User).where(User.id == current_user["id"]))
    user_info = user_result.scalar_one_or_none()
    level = user_info.difficulty_level if user_info else None
    logger.info(f"开始练习: user_id={current_user['id']}, topic_id={request.topic_id}, mode={request.mode}, level={level}")

    service = PracticeService(db)
    return await service.start_practice(
        user_id=current_user["id"],
        topic_id=request.topic_id,
        mode=request.mode,
        year=request.year,
        level=level,
        sort_by=request.sort_by,
    )


@router.post("/submit", response_model=PracticeSubmitResponse)
async def submit_answer(request: PracticeSubmitRequest, db: DBSession, current_user: CurrentUser):
    """Submit answer"""
    logger.info(f"提交答案: user_id={current_user['id']}, question_id={request.question_id}, answer={request.user_answer}")
    service = PracticeService(db)
    result = await service.submit_answer(
        user_id=current_user["id"],
        question_id=request.question_id,
        user_answer=request.user_answer,
        time_spent=request.time_spent,
    )
    logger.info(f"提交答案结果: user_id={current_user['id']}, question_id={request.question_id}, correct={result.is_correct}")
    return result


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


@router.get("/weak-analysis")
async def get_weak_analysis(db: DBSession, user: CurrentUser):
    """获取用户薄弱专题分析"""
    stats = await db.execute(
        select(
            Question.topic_id,
            Topic.title,
            func.count(PracticeRecord.id).label("total"),
            func.sum(cast(PracticeRecord.is_correct, Integer)).label("correct")
        )
        .join(Question, PracticeRecord.question_id == Question.id)
        .join(Topic, Question.topic_id == Topic.id)
        .where(PracticeRecord.user_id == user["id"])
        .group_by(Question.topic_id, Topic.title)
        .order_by(func.sum(cast(PracticeRecord.is_correct, Integer)) / func.count(PracticeRecord.id))
    )
    rows = stats.all()

    weak_topics = []
    recommended_difficulty = 3
    for r in rows:
        rate = (r.correct / r.total * 100) if r.total > 0 else 0
        weak_topics.append({
            "topic_id": r.topic_id,
            "title": r.title,
            "accuracy": round(rate, 1),
            "total": r.total,
        })
        if rate < 50:
            recommended_difficulty = max(1, recommended_difficulty - 1)
        elif rate > 80:
            recommended_difficulty = min(6, recommended_difficulty + 1)

    return {
        "weak_topics": weak_topics[:3],
        "recommended_difficulty": recommended_difficulty,
    }