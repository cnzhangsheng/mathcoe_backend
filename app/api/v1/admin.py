"""
Admin management API - 用户、专题、题目管理
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.api.deps import DBSession
from app.models.user import User
from app.models.topic import Topic
from app.models.question import Question
from app.models.user_progress import UserProgress
from app.models.practice_record import PracticeRecord
from app.schemas.user import UserResponse
from app.schemas.topic import TopicResponse, TopicCreate, TopicUpdate
from app.schemas.question import QuestionResponse, QuestionCreate, QuestionUpdate

router = APIRouter()


# ============ 用户管理 ============

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: DBSession,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str | None = None
):
    """获取用户列表"""
    query = select(User).options(
        noload(User.progress),
        noload(User.practice_records),
        noload(User.favorites),
        noload(User.wrong_questions)
    )
    if keyword:
        query = query.where(User.nickname.ilike(f"%{keyword}%"))
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_detail(user_id: int, db: DBSession):
    """获取用户详情"""
    result = await db.execute(
        select(User).options(
            noload(User.progress),
            noload(User.practice_records),
            noload(User.favorites),
            noload(User.wrong_questions)
        ).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


# ============ 专题管理 ============

@router.get("/topics", response_model=list[TopicResponse])
async def list_topics_admin(db: DBSession):
    """获取专题列表"""
    result = await db.execute(
        select(Topic).options(
            noload(Topic.questions),
            noload(Topic.user_progress)
        )
    )
    return list(result.scalars().all())


@router.post("/topics", response_model=TopicResponse)
async def create_topic(data: TopicCreate, db: DBSession):
    """创建专题"""
    topic = Topic(**data.model_dump())
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic


@router.put("/topics/{topic_id}", response_model=TopicResponse)
async def update_topic(topic_id: int, data: TopicUpdate, db: DBSession):
    """更新专题"""
    result = await db.execute(
        select(Topic).options(
            noload(Topic.questions),
            noload(Topic.user_progress)
        ).where(Topic.id == topic_id)
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="专题不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(topic, key, value)
    await db.commit()
    await db.refresh(topic)
    return topic


@router.delete("/topics/{topic_id}")
async def delete_topic(topic_id: int, db: DBSession):
    """删除专题"""
    result = await db.execute(
        select(Topic).options(
            noload(Topic.questions),
            noload(Topic.user_progress)
        ).where(Topic.id == topic_id)
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="专题不存在")
    await db.delete(topic)
    await db.commit()
    return {"message": "删除成功"}


# ============ 题目管理 ============

@router.get("/questions", response_model=list[QuestionResponse])
async def list_questions_admin(
    db: DBSession,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    topic_id: int | None = None,
    difficulty: str | None = None
):
    """获取题目列表"""
    query = select(Question).options(
        noload(Question.topic),
        noload(Question.practice_records),
        noload(Question.favorites),
        noload(Question.wrong_questions)
    )
    if topic_id:
        query = query.where(Question.topic_id == topic_id)
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/questions", response_model=QuestionResponse)
async def create_question(data: QuestionCreate, db: DBSession):
    """创建题目"""
    question = Question(**data.model_dump())
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(question_id: int, data: QuestionUpdate, db: DBSession):
    """更新题目"""
    result = await db.execute(
        select(Question).options(
            noload(Question.topic),
            noload(Question.practice_records),
            noload(Question.favorites),
            noload(Question.wrong_questions)
        ).where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(question, key, value)
    await db.commit()
    await db.refresh(question)
    return question


@router.delete("/questions/{question_id}")
async def delete_question(question_id: int, db: DBSession):
    """删除题目"""
    result = await db.execute(
        select(Question).options(
            noload(Question.topic),
            noload(Question.practice_records),
            noload(Question.favorites),
            noload(Question.wrong_questions)
        ).where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    await db.delete(question)
    await db.commit()
    return {"message": "删除成功"}


@router.post("/questions/batch-delete")
async def batch_delete_questions(ids: list[int], db: DBSession):
    """批量删除题目"""
    if not ids:
        raise HTTPException(status_code=400, detail="请提供要删除的题目ID")

    deleted_count = 0
    for question_id in ids:
        result = await db.execute(
            select(Question).options(
                noload(Question.topic),
                noload(Question.practice_records),
                noload(Question.favorites),
                noload(Question.wrong_questions)
            ).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        if question:
            await db.delete(question)
            deleted_count += 1

    await db.commit()
    return {"message": f"成功删除 {deleted_count} 道题目", "deleted_count": deleted_count}


@router.get("/questions/count")
async def get_questions_count(db: DBSession, topic_id: int | None = None):
    """获取题目总数"""
    query = select(func.count(Question.id))
    if topic_id:
        query = query.where(Question.topic_id == topic_id)
    result = await db.execute(query)
    return {"total": result.scalar()}


# ============ 统计数据 ============

@router.get("/stats")
async def get_dashboard_stats(db: DBSession):
    """获取仪表盘统计数据"""
    users_count = await db.execute(select(func.count(User.id)))
    users_total = users_count.scalar() or 0

    questions_count = await db.execute(select(func.count(Question.id)))
    questions_total = questions_count.scalar() or 0

    topics_count = await db.execute(select(func.count(Topic.id)))
    topics_total = topics_count.scalar() or 0

    records_count = await db.execute(select(func.count(PracticeRecord.id)))
    records_total = records_count.scalar() or 0

    return {
        "users_total": users_total,
        "questions_total": questions_total,
        "topics_total": topics_total,
        "records_total": records_total
    }


@router.get("/stats/users")
async def get_users_count(db: DBSession):
    """获取用户总数"""
    result = await db.execute(select(func.count(User.id)))
    return {"total": result.scalar()}


@router.get("/stats/questions")
async def get_questions_stats(db: DBSession, topic_id: int | None = None):
    """获取题目统计"""
    query = select(func.count(Question.id))
    if topic_id:
        query = query.where(Question.topic_id == topic_id)
    result = await db.execute(query)
    return {"total": result.scalar()}