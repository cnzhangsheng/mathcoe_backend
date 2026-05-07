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
from app.models.exam_paper import ExamPaper
from app.models.exam_paper_test import ExamPaperTest

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


@router.get("/reports/exam-paper-stats")
async def get_exam_paper_stats_report(db: DBSession):
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
