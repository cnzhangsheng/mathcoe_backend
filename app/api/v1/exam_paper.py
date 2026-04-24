"""
ExamPaper API for miniapp - 用户端考卷接口
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, CurrentUser
from app.models.exam_paper import ExamPaper, ExamPaperQuestion
from app.models.exam_paper_test import ExamPaperTest
from app.models.question import Question
from app.schemas.exam_paper import (
    ExamPaperResponse, ExamPaperWithQuestions,
    ExamPaperTestStart, ExamPaperTestAnswer, ExamPaperTestSubmit,
    ExamPaperTestResponse, ExamPaperTestDetail, ExamPaperTestList
)

router = APIRouter()


# ============ 考卷基础接口 ============

@router.get("", response_model=list[ExamPaperResponse])
async def list_exam_papers(db: DBSession):
    """获取考卷列表"""
    result = await db.execute(select(ExamPaper))
    return list(result.scalars().all())


@router.get("/{exam_paper_id}", response_model=ExamPaperWithQuestions)
async def get_exam_paper(exam_paper_id: int, db: DBSession):
    """获取考卷详情（包含题目列表）"""
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


# ============ 考卷测试接口 ============

@router.post("/{exam_paper_id}/start", response_model=ExamPaperTestResponse)
async def start_exam_paper_test(exam_paper_id: int, db: DBSession, user: CurrentUser):
    """开始考卷测试"""
    # 检查考卷是否存在
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")

    # 获取考卷题目数量
    questions_result = await db.execute(
        select(ExamPaperQuestion).where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
    )
    questions = list(questions_result.scalars().all())

    # 创建测试记录
    test = ExamPaperTest(
        user_id=user["id"],
        exam_paper_id=exam_paper_id,
        total_questions=len(questions),
        started_at=datetime.utcnow(),
        status="in_progress"
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    return ExamPaperTestResponse(
        id=test.id,
        user_id=test.user_id,
        exam_paper_id=test.exam_paper_id,
        exam_paper_title=exam_paper.title,
        total_questions=test.total_questions,
        started_at=test.started_at,
        status=test.status
    )


@router.post("/tests/{test_id}/answer", response_model=ExamPaperTestResponse)
async def submit_test_answer(test_id: int, answer: ExamPaperTestAnswer, db: DBSession, user: CurrentUser):
    """提交单题答案"""
    result = await db.execute(
        select(ExamPaperTest).where(ExamPaperTest.id == test_id, ExamPaperTest.user_id == user["id"])
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="测试记录不存在")

    if test.status == "completed":
        raise HTTPException(status_code=400, detail="测试已结束")

    # 更新答案
    answers = test.answers or {}
    answers[str(answer.question_index)] = answer.user_answer
    test.answers = answers

    await db.commit()
    await db.refresh(test)

    return ExamPaperTestResponse(
        id=test.id,
        user_id=test.user_id,
        exam_paper_id=test.exam_paper_id,
        total_questions=test.total_questions,
        answers=test.answers,
        started_at=test.started_at,
        status=test.status
    )


@router.post("/tests/{test_id}/submit", response_model=ExamPaperTestDetail)
async def submit_exam_paper_test(test_id: int, submit: ExamPaperTestSubmit, db: DBSession, user: CurrentUser):
    """完成考卷测试"""
    result = await db.execute(
        select(ExamPaperTest).where(ExamPaperTest.id == test_id, ExamPaperTest.user_id == user["id"])
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="测试记录不存在")

    if test.status == "completed":
        raise HTTPException(status_code=400, detail="测试已结束")

    # 获取考卷题目和正确答案
    questions_result = await db.execute(
        select(ExamPaperQuestion)
        .options(selectinload(ExamPaperQuestion.question))
        .where(ExamPaperQuestion.exam_paper_id == test.exam_paper_id)
        .order_by(ExamPaperQuestion.sort)
    )
    questions = list(questions_result.scalars().all())

    # 计算得分
    correct_count = 0
    correct_answers = {}
    for i, q in enumerate(questions, 1):
        correct_answers[i] = q.question.answer
        user_answer = submit.answers.get(i)
        if user_answer and user_answer.upper() == q.question.answer.upper():
            correct_count += 1

    score = int((correct_count / len(questions)) * 100) if questions else 0

    # 更新测试记录
    test.answers = {str(k): v for k, v in submit.answers.items()}
    test.correct_count = correct_count
    test.score = score
    test.time_spent = submit.time_spent
    test.finished_at = datetime.utcnow()
    test.status = "completed"

    await db.commit()
    await db.refresh(test)

    # 获取考卷标题
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == test.exam_paper_id))
    paper = paper_result.scalar_one_or_none()

    return ExamPaperTestDetail(
        id=test.id,
        user_id=test.user_id,
        exam_paper_id=test.exam_paper_id,
        exam_paper_title=paper.title if paper else None,
        score=test.score,
        correct_count=test.correct_count,
        total_questions=test.total_questions,
        time_spent=test.time_spent,
        answers=test.answers,
        started_at=test.started_at,
        finished_at=test.finished_at,
        status=test.status,
        correct_answers=correct_answers
    )


@router.get("/tests", response_model=ExamPaperTestList)
async def get_user_tests(db: DBSession, user: CurrentUser, limit: int = 20, offset: int = 0):
    """获取用户测试记录列表"""
    # 查询总数
    count_result = await db.execute(
        select(ExamPaperTest).where(ExamPaperTest.user_id == user["id"])
    )
    all_tests = list(count_result.scalars().all())
    total = len(all_tests)

    # 分页查询
    result = await db.execute(
        select(ExamPaperTest)
        .where(ExamPaperTest.user_id == user["id"])
        .order_by(ExamPaperTest.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    tests = list(result.scalars().all())

    # 获取考卷标题
    items = []
    for test in tests:
        paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == test.exam_paper_id))
        paper = paper_result.scalar_one_or_none()
        items.append(ExamPaperTestResponse(
            id=test.id,
            user_id=test.user_id,
            exam_paper_id=test.exam_paper_id,
            exam_paper_title=paper.title if paper else None,
            score=test.score,
            correct_count=test.correct_count,
            total_questions=test.total_questions,
            time_spent=test.time_spent,
            answers=test.answers,
            started_at=test.started_at,
            finished_at=test.finished_at,
            status=test.status
        ))

    return ExamPaperTestList(total=total, items=items)


@router.get("/tests/{test_id}", response_model=ExamPaperTestDetail)
async def get_test_detail(test_id: int, db: DBSession, user: CurrentUser):
    """获取测试记录详情"""
    result = await db.execute(
        select(ExamPaperTest).where(ExamPaperTest.id == test_id, ExamPaperTest.user_id == user["id"])
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="测试记录不存在")

    # 获取考卷标题和正确答案
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == test.exam_paper_id))
    paper = paper_result.scalar_one_or_none()

    questions_result = await db.execute(
        select(ExamPaperQuestion)
        .options(selectinload(ExamPaperQuestion.question))
        .where(ExamPaperQuestion.exam_paper_id == test.exam_paper_id)
        .order_by(ExamPaperQuestion.sort)
    )
    questions = list(questions_result.scalars().all())

    correct_answers = {i: q.question.answer for i, q in enumerate(questions, 1)}

    return ExamPaperTestDetail(
        id=test.id,
        user_id=test.user_id,
        exam_paper_id=test.exam_paper_id,
        exam_paper_title=paper.title if paper else None,
        score=test.score,
        correct_count=test.correct_count,
        total_questions=test.total_questions,
        time_spent=test.time_spent,
        answers=test.answers,
        started_at=test.started_at,
        finished_at=test.finished_at,
        status=test.status,
        correct_answers=correct_answers
    )