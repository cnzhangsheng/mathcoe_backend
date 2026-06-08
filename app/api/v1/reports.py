"""
Reports API - 运营报表
"""
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import select, func, cast, Date, desc
from sqlalchemy.sql import and_

from app.api.deps import DBSession, AdminUser
from app.models.question import Question
from app.models.practice_record import PracticeRecord
from app.models.favorite import Favorite
from app.models.topic import Topic

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/reports/question-ranking")
async def get_question_ranking_report(admin: AdminUser, db: DBSession):
    """题目排行：按难度级别统计热门 TOP20、收藏 TOP20"""
    levels = [1, 2, 3]
    result = {}

    for level in levels:
        # 热门题目 TOP20（按做题次数）
        hot_result = await db.execute(
            select(
                Question.id,
                Question.title,
                Question.difficulty_level,
                Question.status,
                Question.content,
                Topic.id.label("topic_id"),
                Topic.title.label("topic_title"),
                func.count(func.distinct(PracticeRecord.user_id)).label("practice_count"),
                func.count(func.distinct(PracticeRecord.user_id)).label("user_count"),
            )
            .join(Question, PracticeRecord.question_id == Question.id)
            .join(Topic, Topic.id == Question.topic_id, isouter=True)
            .where(Question.difficulty_level == level)
            .group_by(Question.id, Question.title, Question.difficulty_level, Question.status, Question.content, Topic.id, Topic.title)
            .order_by(desc("practice_count"))
            .limit(20)
        )
        hot_rows = hot_result.all()

        hot_questions = []
        for r in hot_rows:
            content_text = ""
            if r.content and isinstance(r.content, dict):
                content_text = r.content.get("text", "")
            hot_questions.append({
                "id": r.id,
                "title": r.title,
                "content": content_text or r.title,
                "difficulty_level": r.difficulty_level,
                "topic_title": r.topic_title or "未分类",
                "practice_count": r.practice_count,
                "user_count": r.user_count,
            })

        # 收藏题目 TOP20（按收藏次数）
        fav_result = await db.execute(
            select(
                Question.id,
                Question.title,
                Question.difficulty_level,
                Question.status,
                Question.content,
                Topic.id.label("topic_id"),
                Topic.title.label("topic_title"),
                func.count(Favorite.id).label("favorite_count"),
                func.count(func.distinct(Favorite.user_id)).label("fav_user_count"),
            )
            .join(Question, Favorite.question_id == Question.id)
            .join(Topic, Topic.id == Question.topic_id, isouter=True)
            .where(Question.difficulty_level == level)
            .group_by(Question.id, Question.title, Question.difficulty_level, Question.status, Question.content, Topic.id, Topic.title)
            .order_by(desc("favorite_count"))
            .limit(20)
        )
        fav_rows = fav_result.all()

        favorite_questions = []
        for r in fav_rows:
            content_text = ""
            if r.content and isinstance(r.content, dict):
                content_text = r.content.get("text", "")
            favorite_questions.append({
                "id": r.id,
                "title": r.title,
                "content": content_text or r.title,
                "difficulty_level": r.difficulty_level,
                "topic_title": r.topic_title or "未分类",
                "favorite_count": r.favorite_count,
                "fav_user_count": r.fav_user_count,
            })

        result[str(level)] = {
            "hot_questions": hot_questions,
            "favorite_questions": favorite_questions,
        }

    return result


@router.get("/reports/practice-trend")
async def get_practice_trend_report(
    admin: AdminUser,
    db: DBSession,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
):
    """答题记录趋势报表：按日统计答题总量和参与用户数"""
    now = datetime.now()
    start_date = now - timedelta(days=days - 1)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # 按日期分组统计
    result = await db.execute(
        select(
            cast(PracticeRecord.created_at, Date).label("date"),
            func.count(PracticeRecord.id).label("practice_count"),
            func.count(func.distinct(PracticeRecord.user_id)).label("user_count"),
        )
        .where(PracticeRecord.created_at >= start_date)
        .group_by(cast(PracticeRecord.created_at, Date))
        .order_by(cast(PracticeRecord.created_at, Date))
    )
    rows = result.all()

    # 将查询结果转为字典，便于补零
    date_map: dict[str, dict] = {}
    for r in rows:
        date_str = str(r.date)
        date_map[date_str] = {
            "date": date_str,
            "practice_count": r.practice_count,
            "user_count": r.user_count,
        }

    # 补全无数据的日期
    items: list[dict] = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        if date_str in date_map:
            items.append(date_map[date_str])
        else:
            items.append({
                "date": date_str,
                "practice_count": 0,
                "user_count": 0,
            })

    return {"items": items}
