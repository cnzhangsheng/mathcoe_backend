"""
Reports API - 运营报表
"""
import logging
from fastapi import APIRouter
from sqlalchemy import select, func, desc, Integer
from sqlalchemy.sql import and_

from app.api.deps import DBSession
from app.models.question import Question
from app.models.practice_record import PracticeRecord
from app.models.like import Like
from app.models.favorite import Favorite
from app.models.topic import Topic

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/reports/question-type")
async def get_question_type_report(db: DBSession):
    """用户题型偏好报表：各题型做题占比、点赞率、收藏率"""
    # 查询各题型的做题、点赞、收藏统计
    result = await db.execute(
        select(
            Question.question_type,
            func.count(func.distinct(PracticeRecord.id)).label("practice_count"),
            func.count(func.distinct(Like.id)).label("like_count"),
            func.count(func.distinct(Favorite.id)).label("favorite_count"),
        )
        .outerjoin(PracticeRecord, PracticeRecord.question_id == Question.id)
        .outerjoin(Like, Like.question_id == Question.id)
        .outerjoin(Favorite, Favorite.question_id == Question.id)
        .group_by(Question.question_type)
    )
    rows = result.all()

    # 计算总量
    total_practice = sum(r.practice_count for r in rows) or 1
    type_labels = {"single": "单选题", "multiple": "多选题"}

    items = []
    for r in rows:
        practice_count = r.practice_count
        like_rate = round(r.like_count / practice_count * 100, 1) if practice_count > 0 else 0
        favorite_rate = round(r.favorite_count / practice_count * 100, 1) if practice_count > 0 else 0
        items.append({
            "question_type": r.question_type,
            "type_label": type_labels.get(r.question_type, r.question_type),
            "practice_count": practice_count,
            "practice_ratio": round(practice_count / total_practice * 100, 1),
            "like_count": r.like_count,
            "like_rate": like_rate,
            "favorite_count": r.favorite_count,
            "favorite_rate": favorite_rate,
        })

    return {"items": items, "total_practice": total_practice}


@router.get("/reports/topic-preference")
async def get_topic_preference_report(db: DBSession):
    """知识点偏好运营报表：各知识点做题人次、收藏TOP、点赞TOP"""
    # 各知识点统计
    result = await db.execute(
        select(
            Topic.id,
            Topic.title,
            func.count(func.distinct(PracticeRecord.id)).label("practice_count"),
            func.count(func.distinct(PracticeRecord.user_id)).label("user_count"),
            func.count(func.distinct(Like.id)).label("like_count"),
            func.count(func.distinct(Favorite.id)).label("favorite_count"),
        )
        .join(Question, Question.topic_id == Topic.id)
        .outerjoin(PracticeRecord, PracticeRecord.question_id == Question.id)
        .outerjoin(Like, Like.question_id == Question.id)
        .outerjoin(Favorite, Favorite.question_id == Question.id)
        .group_by(Topic.id, Topic.title)
        .order_by(desc("practice_count"))
    )
    rows = result.all()

    items = []
    for r in rows:
        items.append({
            "topic_id": r.id,
            "topic_title": r.title,
            "practice_count": r.practice_count,
            "user_count": r.user_count,
            "like_count": r.like_count,
            "favorite_count": r.favorite_count,
        })

    # 收藏 TOP 5
    top_favorites = sorted(items, key=lambda x: x["favorite_count"], reverse=True)[:5]

    # 点赞 TOP 5
    top_likes = sorted(items, key=lambda x: x["like_count"], reverse=True)[:5]

    return {
        "items": items,
        "top_favorites": top_favorites,
        "top_likes": top_likes,
    }
