"""
Admin management API - 用户、专题、题目、考卷管理
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.api.deps import DBSession
from app.models.user import User
from app.models.topic import Topic
from app.models.question import Question
from app.models.exam_paper import ExamPaper, ExamPaperQuestion
from app.models.practice_record import PracticeRecord
from app.schemas.user import UserResponse
from app.schemas.topic import TopicResponse, TopicCreate, TopicUpdate
from app.schemas.question import QuestionResponse, QuestionCreate, QuestionUpdate
from app.schemas.exam_paper import (
    ExamPaperResponse, ExamPaperCreate, ExamPaperUpdate, ExamPaperWithQuestions,
    ExamPaperQuestionCreate, ExamPaperQuestionUpdate, ExamPaperQuestionResponse
)

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
        select(User).where(User.id == user_id)
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
    level: int | None = None
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
    if level:
        query = query.where(Question.difficulty_level == level)
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


# ============ 考卷管理 ============

@router.get("/exam-papers", response_model=list[ExamPaperResponse])
async def list_exam_papers(
    db: DBSession,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    difficulty_level: int | None = None,
    paper_type: str | None = None
):
    """获取考卷列表"""
    query = select(ExamPaper)
    if difficulty_level:
        query = query.where(ExamPaper.difficulty_level == difficulty_level)
    if paper_type:
        query = query.where(ExamPaper.paper_type == paper_type)
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/exam-papers", response_model=ExamPaperResponse)
async def create_exam_paper(data: ExamPaperCreate, db: DBSession):
    """创建考卷"""
    exam_paper = ExamPaper(**data.model_dump())
    db.add(exam_paper)
    await db.commit()
    await db.refresh(exam_paper)
    return exam_paper


@router.get("/exam-papers/{exam_paper_id}", response_model=ExamPaperWithQuestions)
async def get_exam_paper_detail(exam_paper_id: int, db: DBSession):
    """获取考卷详情（包含题目列表）"""
    # 获取考卷
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")

    # 手动加载题目并排序
    questions_result = await db.execute(
        select(ExamPaperQuestion)
        .options(selectinload(ExamPaperQuestion.question))
        .where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
        .order_by(ExamPaperQuestion.sort)
    )
    exam_paper.questions = list(questions_result.scalars().all())
    return exam_paper


@router.put("/exam-papers/{exam_paper_id}", response_model=ExamPaperResponse)
async def update_exam_paper(exam_paper_id: int, data: ExamPaperUpdate, db: DBSession):
    """更新考卷"""
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(exam_paper, key, value)
    await db.commit()
    await db.refresh(exam_paper)
    return exam_paper


@router.delete("/exam-papers/{exam_paper_id}")
async def delete_exam_paper(exam_paper_id: int, db: DBSession):
    """删除考卷（同时删除关联的题目）"""
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")
    # 删除关联的题目
    await db.execute(delete(ExamPaperQuestion).where(ExamPaperQuestion.exam_paper_id == exam_paper_id))
    await db.delete(exam_paper)
    await db.commit()
    return {"message": "删除成功"}


# ============ 考卷题目管理 ============

@router.get("/exam-papers/{exam_paper_id}/questions", response_model=list[ExamPaperQuestionResponse])
async def list_exam_paper_questions(exam_paper_id: int, db: DBSession):
    """获取考卷题目列表"""
    result = await db.execute(
        select(ExamPaperQuestion)
        .options(selectinload(ExamPaperQuestion.question))
        .where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
        .order_by(ExamPaperQuestion.sort)
    )
    return list(result.scalars().all())


@router.post("/exam-papers/{exam_paper_id}/questions", response_model=ExamPaperQuestionResponse)
async def add_question_to_exam_paper(exam_paper_id: int, data: ExamPaperQuestionCreate, db: DBSession):
    """添加题目到考卷"""
    # 检查考卷是否存在
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = paper_result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")

    # 检查题目是否存在
    question_result = await db.execute(select(Question).where(Question.id == data.question_id))
    question = question_result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    # 检查题目数量限制
    count_result = await db.execute(
        select(func.count(ExamPaperQuestion.id)).where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
    )
    current_count = count_result.scalar() or 0
    if current_count >= exam_paper.total_questions:
        raise HTTPException(status_code=400, detail=f"考卷最多只能添加{exam_paper.total_questions}题")

    # 检查题目是否已添加
    existing_result = await db.execute(
        select(ExamPaperQuestion)
        .where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
        .where(ExamPaperQuestion.question_id == data.question_id)
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="该题目已添加到考卷中")

    # 计算新的排序号
    if data.sort == 1:  # 默认排序，自动计算
        max_sort_result = await db.execute(
            select(func.max(ExamPaperQuestion.sort)).where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
        )
        max_sort = max_sort_result.scalar() or 0
        data.sort = max_sort + 1

    exam_paper_question = ExamPaperQuestion(
        exam_paper_id=exam_paper_id,
        question_id=data.question_id,
        sort=data.sort
    )
    db.add(exam_paper_question)
    await db.commit()
    # 重新查询以加载 question 关系
    result = await db.execute(
        select(ExamPaperQuestion)
        .options(selectinload(ExamPaperQuestion.question))
        .where(ExamPaperQuestion.id == exam_paper_question.id)
    )
    return result.scalar_one()


@router.delete("/exam-papers/{exam_paper_id}/questions/{question_id}")
async def remove_question_from_exam_paper(exam_paper_id: int, question_id: int, db: DBSession):
    """从考卷移除题目"""
    result = await db.execute(
        select(ExamPaperQuestion)
        .where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
        .where(ExamPaperQuestion.question_id == question_id)
    )
    exam_paper_question = result.scalar_one_or_none()
    if not exam_paper_question:
        raise HTTPException(status_code=404, detail="题目不在考卷中")
    await db.delete(exam_paper_question)
    await db.commit()
    return {"message": "移除成功"}


@router.post("/exam-papers/{exam_paper_id}/questions/sort")
async def update_exam_paper_questions_sort(exam_paper_id: int, sorts: list[dict], db: DBSession):
    """更新考卷题目排序
    sorts: [{"id": 1, "sort": 1}, {"id": 2, "sort": 2}, ...]
    """
    for item in sorts:
        result = await db.execute(
            select(ExamPaperQuestion)
            .where(ExamPaperQuestion.id == item["id"])
            .where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
        )
        epq = result.scalar_one_or_none()
        if epq:
            epq.sort = item["sort"]
    await db.commit()
    return {"message": "排序更新成功"}