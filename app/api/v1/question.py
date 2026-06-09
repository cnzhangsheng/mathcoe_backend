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


from fastapi import Query
from app.repositories.question_repo import QuestionRepository


@router.get("/search")
async def search_questions(
    keyword: str = Query(""),
    level: int | None = Query(None),
    topic_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    db: DBSession = None,
    user: UserOrNone = None,
):
    """按题目内容模糊搜索"""
    if not keyword.strip():
        return {"items": [], "total": 0, "page": page, "size": size}

    repo = QuestionRepository(db)
    questions, total = await repo.search_by_content(keyword.strip(), level, topic_id, page, size)

    items = []
    for q in questions:
        content_text = ""
        if q.content and isinstance(q.content, dict):
            content_text = q.content.get("text", "")
        items.append({
            "id": q.id,
            "content": content_text,
            "difficulty_level": q.difficulty_level,
            "topic_title": q.topic.title if q.topic else "未分类",
            "question_type": q.question_type,
        })

    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/rankings")
async def get_question_rankings(
    level: int = Query(1, ge=1, le=3),
    db: DBSession = None,
    user: UserOrNone = None,
):
    """获取指定Level的收藏TOP20和易错TOP20"""
    repo = QuestionRepository(db)
    result = await repo.get_rankings(level)

    hot_questions = []
    for q, fav_count in result["hot_rows"]:
        content_text = ""
        if q.content and isinstance(q.content, dict):
            content_text = q.content.get("text", "")
        hot_questions.append({
            "id": q.id,
            "content": content_text,
            "difficulty_level": q.difficulty_level,
            "topic_title": q.topic.title if q.topic else "未分类",
            "favorite_count": fav_count,
        })

    wrong_questions = []
    for q, total_users, wrong_users in result["wrong_rows"]:
        content_text = ""
        if q.content and isinstance(q.content, dict):
            content_text = q.content.get("text", "")
        error_rate = round(wrong_users / total_users * 100, 1) if total_users > 0 else 0
        wrong_questions.append({
            "id": q.id,
            "content": content_text,
            "difficulty_level": q.difficulty_level,
            "topic_title": q.topic.title if q.topic else "未分类",
            "error_rate": error_rate,
            "wrong_count": wrong_users,
            "total_attempts": total_users,
        })

    return {
        "hot_questions": hot_questions,
        "wrong_questions": wrong_questions,
    }


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: DBSession):
    """Get question by ID"""
    service = QuestionService(db)
    return await service.get_question(question_id)