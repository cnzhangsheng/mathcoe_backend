"""
Reports API - 运营报表
"""
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import select, func, cast, Date
from sqlalchemy.sql import and_

from app.api.deps import DBSession, AdminUser
from app.models.question import Question
from app.models.practice_record import PracticeRecord
from app.models.favorite import Favorite
from app.models.topic import Topic
from app.models.exam_paper import ExamPaper
from app.models.exam_paper_test import ExamPaperTest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/reports/question-type")
async def get_question_type_report(admin: AdminUser, db: DBSession):
    """用户题型偏好报表：各题型做题占比、收藏率"""
    result = await db.execute(
        select(
            Question.question_type,
            func.count(func.distinct(PracticeRecord.id)).label("practice_count"),
            func.count(func.distinct(Favorite.id)).label("favorite_count"),
        )
        .outerjoin(PracticeRecord, PracticeRecord.question_id == Question.id)
        .outerjoin(Favorite, Favorite.question_id == Question.id)
        .group_by(Question.question_type)
    )
    rows = result.all()

    total_practice = sum(r.practice_count for r in rows) or 1
    type_labels = {"single": "单选题", "multiple": "多选题"}

    items = []
    for r in rows:
        practice_count = r.practice_count
        favorite_rate = round(r.favorite_count / practice_count * 100, 1) if practice_count > 0 else 0
        items.append({
            "question_type": r.question_type,
            "type_label": type_labels.get(r.question_type, r.question_type),
            "practice_count": practice_count,
            "practice_ratio": round(practice_count / total_practice * 100, 1),
            "favorite_count": r.favorite_count,
            "favorite_rate": favorite_rate,
        })

    return {"items": items, "total_practice": total_practice}


@router.get("/reports/topic-preference")
async def get_topic_preference_report(admin: AdminUser, db: DBSession):
    """知识点偏好运营报表：各知识点做题人次、收藏TOP"""
    result = await db.execute(
        select(
            Topic.id,
            Topic.title,
            func.count(func.distinct(PracticeRecord.id)).label("practice_count"),
            func.count(func.distinct(PracticeRecord.user_id)).label("user_count"),
            func.count(func.distinct(Favorite.id)).label("favorite_count"),
        )
        .join(Question, Question.topic_id == Topic.id)
        .outerjoin(PracticeRecord, PracticeRecord.question_id == Question.id)
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
            "favorite_count": r.favorite_count,
        })

    # 收藏 TOP 5
    top_favorites = sorted(items, key=lambda x: x["favorite_count"], reverse=True)[:5]

    return {
        "items": items,
        "top_favorites": top_favorites,
    }


@router.get("/reports/exam-paper-stats")
async def get_exam_paper_stats_report(admin: AdminUser, db: DBSession):
    """考卷用户统计数据：考卷维度统计"""
    # 整体考卷测试统计
    total_result = await db.execute(select(func.count(ExamPaperTest.id)))
    total_tests = total_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(ExamPaperTest.id)).where(ExamPaperTest.status == "completed")
    )
    completed_tests = completed_result.scalar() or 0

    users_result = await db.execute(select(func.count(func.distinct(ExamPaperTest.user_id))))
    total_users = users_result.scalar() or 0

    avg_score_result = await db.execute(
        select(func.avg(ExamPaperTest.score.cast(Integer))).where(ExamPaperTest.status == "completed")
    )
    avg_score = round(float(avg_score_result.scalar() or 0), 1)

    # 按考卷类型统计
    type_result = await db.execute(
        select(
            ExamPaper.paper_type,
            func.count(ExamPaperTest.id).label("test_count"),
            func.sum(func.cast(ExamPaperTest.status == "completed", Integer)).label("completed_count"),
            func.avg(ExamPaperTest.score.cast(Integer)).label("avg_score"),
        )
        .join(ExamPaper, ExamPaper.id == ExamPaperTest.exam_paper_id)
        .group_by(ExamPaper.paper_type)
    )
    type_rows = type_result.all()
    type_labels = {"daily": "每日一练", "mock": "模拟卷", "topic": "专项训练"}

    type_stats = []
    for r in type_rows:
        type_stats.append({
            "paper_type": r.paper_type,
            "type_label": type_labels.get(r.paper_type, r.paper_type),
            "test_count": r.test_count,
            "completed_count": r.completed_count or 0,
            "completion_rate": round((r.completed_count or 0) / r.test_count * 100, 1) if r.test_count > 0 else 0,
            "avg_score": round(float(r.avg_score or 0), 1),
        })

    # 热门考卷 TOP 10（按测试次数）
    top_result = await db.execute(
        select(
            ExamPaper.id,
            ExamPaper.title,
            ExamPaper.paper_type,
            func.count(ExamPaperTest.id).label("test_count"),
            func.avg(ExamPaperTest.score.cast(Integer)).label("avg_score"),
            func.count(func.distinct(ExamPaperTest.user_id)).label("user_count"),
        )
        .join(ExamPaperTest, ExamPaperTest.exam_paper_id == ExamPaper.id)
        .group_by(ExamPaper.id, ExamPaper.title, ExamPaper.paper_type)
        .order_by(desc("test_count"))
        .limit(10)
    )
    top_rows = top_result.all()

    top_papers = []
    for r in top_rows:
        top_papers.append({
            "id": r.id,
            "title": r.title,
            "paper_type": r.paper_type,
            "type_label": type_labels.get(r.paper_type, r.paper_type),
            "test_count": r.test_count,
            "avg_score": round(float(r.avg_score or 0), 1),
            "user_count": r.user_count,
        })

    # 分数分布（考卷测试的得分分布）
    score_distribution = await db.execute(
        select(
            func.floor(ExamPaperTest.score / 10).label("bucket"),
            func.count(ExamPaperTest.id).label("count"),
        )
        .where(ExamPaperTest.status == "completed")
        .where(ExamPaperTest.score.isnot(None))
        .group_by("bucket")
        .order_by("bucket")
    )
    dist_rows = score_distribution.all()
    score_dist = []
    for r in dist_rows:
        bucket_start = r.bucket * 10
        score_dist.append({
            "range": f"{bucket_start}-{bucket_start + 9}",
            "count": r.count,
        })

    return {
        "total_tests": total_tests,
        "completed_tests": completed_tests,
        "total_users": total_users,
        "avg_score": avg_score,
        "type_stats": type_stats,
        "top_papers": top_papers,
        "score_distribution": score_dist,
    }


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
