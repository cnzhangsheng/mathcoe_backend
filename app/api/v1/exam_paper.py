"""
ExamPaper API for miniapp - 用户端考卷接口
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, CurrentUser
from app.models.exam_paper import ExamPaper, ExamPaperQuestion
from app.models.exam_paper_test import ExamPaperTest
from app.models.exam_paper_test_answer import TestAnswerRecord
from app.models.question import Question
from app.schemas.exam_paper import (
    ExamPaperResponse, ExamPaperWithQuestions,
    ExamPaperTestStart, ExamPaperTestAnswer, ExamPaperTestSubmit,
    ExamPaperTestResponse, ExamPaperTestDetail, ExamPaperTestList,
    ExamPaperTestAnswerResponse, UserWrongQuestion
)

router = APIRouter()


# ============ 考卷测试接口 ============
# Note: /tests routes must come BEFORE /{exam_paper_id} to avoid route conflicts

@router.get("/tests", response_model=ExamPaperTestList)
async def get_user_tests(db: DBSession, user: CurrentUser, limit: int = 20, offset: int = 0):
    """获取用户测试记录列表"""
    # 查询总数
    count_result = await db.execute(
        select(func.count()).select_from(ExamPaperTest).where(ExamPaperTest.user_id == user["id"])
    )
    total = count_result.scalar() or 0

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

    # 获取考卷标题
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == test.exam_paper_id))
    paper = paper_result.scalar_one_or_none()

    # 从 exam_paper_test_answers 获取答题记录
    answers_result = await db.execute(
        select(TestAnswerRecord)
        .where(TestAnswerRecord.test_id == test_id)
        .order_by(TestAnswerRecord.question_index)
    )
    answer_records = list(answers_result.scalars().all())

    # 构建正确答案汇总
    correct_answers_summary = {r.question_index: r.correct_answer for r in answer_records}

    return ExamPaperTestDetail(
        id=test.id,
        user_id=test.user_id,
        exam_paper_id=test.exam_paper_id,
        exam_paper_title=paper.title if paper else None,
        score=test.score,
        correct_count=test.correct_count,
        total_questions=test.total_questions,
        time_spent=test.time_spent,
        started_at=test.started_at,
        finished_at=test.finished_at,
        status=test.status,
        correct_answers_summary=correct_answers_summary
    )


@router.post("/tests/{test_id}/submit", response_model=ExamPaperTestDetail)
async def submit_exam_paper_test(test_id: int, submit: ExamPaperTestSubmit, db: DBSession, user: CurrentUser):
    """完成考卷测试（通过test_id提交）"""
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

    # 计算得分并创建答题记录
    correct_count = 0
    correct_answers_summary = {}
    answer_records = []

    for i, q in enumerate(questions, 1):
        question_id = q.question_id
        correct_answer = q.question.answer
        user_answer = submit.answers.get(i)

        correct_answers_summary[i] = correct_answer

        is_correct = user_answer and user_answer.upper() == correct_answer.upper()
        if is_correct:
            correct_count += 1

        answer_record = TestAnswerRecord(
            test_id=test.id,
            user_id=user["id"],
            exam_paper_id=test.exam_paper_id,
            question_index=i,
            question_id=question_id,
            user_answer=user_answer or "",
            correct_answer=correct_answer,
            is_correct=is_correct
        )
        answer_records.append(answer_record)

    score = int((correct_count / len(questions)) * 100) if questions else 0

    # 更新测试记录
    test.correct_count = correct_count
    test.score = score
    test.time_spent = submit.time_spent
    test.finished_at = datetime.utcnow()
    test.status = "completed"

    db.add_all(answer_records)
    await db.commit()

    # 获取考卷标题
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == test.exam_paper_id))
    paper = paper_result.scalar_one_or_none()

    return ExamPaperTestDetail(
        id=test.id,
        user_id=test.user_id,
        exam_paper_id=test.exam_paper_id,
        exam_paper_title=paper.title if paper else None,
        score=score,
        correct_count=correct_count,
        total_questions=test.total_questions,
        time_spent=submit.time_spent,
        started_at=test.started_at,
        finished_at=datetime.utcnow(),
        status="completed",
        correct_answers_summary=correct_answers_summary
    )


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


@router.post("/{exam_paper_id}/start", response_model=ExamPaperTestResponse)
async def start_exam_paper_test(exam_paper_id: int, db: DBSession, user: CurrentUser):
    """开始考卷测试（预创建测试记录）"""
    # 检查考卷是否存在
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")

    # 检查是否已有进行中的测试记录（唯一约束检查）
    existing_test = await db.execute(
        select(ExamPaperTest).where(
            ExamPaperTest.user_id == user["id"],
            ExamPaperTest.exam_paper_id == exam_paper_id,
            ExamPaperTest.status == "in_progress"
        )
    )
    existing = existing_test.scalar_one_or_none()
    if existing:
        return ExamPaperTestResponse(
            id=existing.id,
            user_id=existing.user_id,
            exam_paper_id=existing.exam_paper_id,
            exam_paper_title=exam_paper.title,
            total_questions=existing.total_questions,
            started_at=existing.started_at,
            status=existing.status
        )

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


@router.post("/{exam_paper_id}/submit", response_model=ExamPaperTestDetail)
async def submit_exam_paper_direct(exam_paper_id: int, submit: ExamPaperTestSubmit, db: DBSession, user: CurrentUser):
    """直接提交考卷测试（无需预创建，一次性创建并完成）"""
    # 检查考卷是否存在
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")

    # 检查是否已有记录，如果有则删除旧记录（保证user_id+exam_paper_id唯一）
    existing_test = await db.execute(
        select(ExamPaperTest).where(
            ExamPaperTest.user_id == user["id"],
            ExamPaperTest.exam_paper_id == exam_paper_id
        )
    )
    existing = existing_test.scalar_one_or_none()
    if existing:
        # 先删除关联的答题记录
        await db.execute(
            delete(TestAnswerRecord).where(TestAnswerRecord.test_id == existing.id)
        )
        # 再删除测试记录
        await db.execute(
            delete(ExamPaperTest).where(ExamPaperTest.id == existing.id)
        )
        # 必须先提交删除操作，否则唯一约束会冲突
        await db.commit()

    # 获取考卷题目和正确答案
    questions_result = await db.execute(
        select(ExamPaperQuestion)
        .options(selectinload(ExamPaperQuestion.question))
        .where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
        .order_by(ExamPaperQuestion.sort)
    )
    questions = list(questions_result.scalars().all())

    if not questions:
        raise HTTPException(status_code=400, detail="考卷无题目")

    # 计算得分并创建答题记录
    correct_count = 0
    correct_answers_summary = {}
    answer_records = []

    for i, q in enumerate(questions, 1):
        question_id = q.question_id
        correct_answer = q.question.answer
        user_answer = submit.answers.get(i)

        correct_answers_summary[i] = correct_answer

        is_correct = user_answer and user_answer.upper() == correct_answer.upper()
        if is_correct:
            correct_count += 1

        answer_record = TestAnswerRecord(
            test_id=0,  # 临时值，flush后会更新
            user_id=user["id"],
            exam_paper_id=exam_paper_id,
            question_index=i,
            question_id=question_id,
            user_answer=user_answer or "",
            correct_answer=correct_answer,
            is_correct=is_correct
        )
        answer_records.append(answer_record)

    score = int((correct_count / len(questions)) * 100) if questions else 0

    # 创建测试记录
    now = datetime.utcnow()
    test = ExamPaperTest(
        user_id=user["id"],
        exam_paper_id=exam_paper_id,
        total_questions=len(questions),
        correct_count=correct_count,
        score=score,
        time_spent=submit.time_spent,
        started_at=now,
        finished_at=now,
        status="completed"
    )
    db.add(test)
    await db.flush()  # 获取 test.id

    # 更新答题记录的 test_id
    for record in answer_records:
        record.test_id = test.id

    db.add_all(answer_records)
    await db.commit()

    # 获取考卷标题（commit后重新查询）
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    paper = paper_result.scalar_one_or_none()

    return ExamPaperTestDetail(
        id=test.id,
        user_id=test.user_id,
        exam_paper_id=test.exam_paper_id,
        exam_paper_title=paper.title if paper else None,
        score=score,
        correct_count=correct_count,
        total_questions=len(questions),
        time_spent=submit.time_spent,
        started_at=now,
        finished_at=now,
        status="completed",
        correct_answers_summary=correct_answers_summary
    )


# ============ 答题统计接口 ============

@router.get("/tests/{test_id}/answers", response_model=list[ExamPaperTestAnswerResponse])
async def get_test_answers(test_id: int, db: DBSession, user: CurrentUser):
    """获取某次测试的答题记录列表"""
    # 验证测试记录属于当前用户
    test_result = await db.execute(
        select(ExamPaperTest).where(ExamPaperTest.id == test_id, ExamPaperTest.user_id == user["id"])
    )
    test = test_result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="测试记录不存在")

    # 查询答题记录
    result = await db.execute(
        select(TestAnswerRecord)
        .where(TestAnswerRecord.test_id == test_id)
        .order_by(TestAnswerRecord.question_index)
    )
    answers = list(result.scalars().all())

    return [ExamPaperTestAnswerResponse.model_validate(a) for a in answers]


@router.get("/wrong-questions", response_model=list[UserWrongQuestion])
async def get_user_wrong_questions(db: DBSession, user: CurrentUser, limit: int = 50):
    """获取用户错题本（按错误次数排序）"""
    # 查询用户答错的题目统计
    result = await db.execute(
        select(
            TestAnswerRecord.question_id,
            func.count().filter(TestAnswerRecord.is_correct == False).label("wrong_count"),
            func.count().filter(TestAnswerRecord.is_correct == True).label("correct_count"),
            func.max(TestAnswerRecord.created_at).filter(TestAnswerRecord.is_correct == False).label("last_wrong_at")
        )
        .where(TestAnswerRecord.user_id == user["id"])
        .group_by(TestAnswerRecord.question_id)
        .having(func.count().filter(TestAnswerRecord.is_correct == False) > 0)
        .order_by(func.count().filter(TestAnswerRecord.is_correct == False).desc())
        .limit(limit)
    )
    stats = result.all()

    # 获取题目详情
    wrong_questions = []
    for stat in stats:
        question_result = await db.execute(
            select(Question).where(Question.id == stat.question_id)
        )
        question = question_result.scalar_one_or_none()

        wrong_questions.append(UserWrongQuestion(
            question_id=stat.question_id,
            question_title=question.title if question else None,
            correct_answer=question.answer if question else "",
            wrong_count=stat.wrong_count,
            last_wrong_at=stat.last_wrong_at,
            question=question
        ))

    return wrong_questions


@router.get("/stats/question-error-rate")
async def get_question_error_rate(db: DBSession, exam_paper_id: int | None = None, limit: int = 20):
    """获取题目错误率统计（用于分析哪些题目最难）"""
    # 构建查询
    query = select(
        TestAnswerRecord.question_id,
        func.count().filter(TestAnswerRecord.is_correct == False).label("wrong_count"),
        func.count().filter(TestAnswerRecord.is_correct == True).label("correct_count"),
        func.count().label("total_count")
    )

    if exam_paper_id:
        query = query.where(TestAnswerRecord.exam_paper_id == exam_paper_id)

    query = query.group_by(TestAnswerRecord.question_id).order_by(
        (func.count().filter(TestAnswerRecord.is_correct == False) / func.count()).desc()
    ).limit(limit)

    result = await db.execute(query)
    stats = result.all()

    return [
        {
            "question_id": s.question_id,
            "wrong_count": s.wrong_count,
            "correct_count": s.correct_count,
            "total_count": s.total_count,
            "wrong_rate": round((s.wrong_count / s.total_count) * 100, 2) if s.total_count > 0 else 0
        }
        for s in stats
    ]