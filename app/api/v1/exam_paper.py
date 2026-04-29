"""
ExamPaper API for miniapp - 用户端考卷接口
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func, delete, insert, and_, Integer
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, CurrentUser
from app.models.exam_paper import ExamPaper, ExamPaperQuestion
from app.models.exam_paper_test import ExamPaperTest
from app.models.exam_paper_test_answer import TestAnswerRecord
from app.models.question import Question
from app.models.topic import Topic
from app.models.favorite import WrongQuestion
from app.models.practice_record import PracticeRecord
from app.models.user import User
from app.schemas.exam_paper import (
    ExamPaperResponse, ExamPaperWithQuestions,
    ExamPaperTestStart, ExamPaperTestAnswer, ExamPaperTestSubmit,
    ExamPaperTestResponse, ExamPaperTestDetail, ExamPaperTestList,
    ExamPaperTestAnswerResponse, UserWrongQuestion, ExamPaperTestReport
)
from app.utils.id_generator import short_id

logger = logging.getLogger(__name__)
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


@router.get("/tests/{test_id}/report", response_model=ExamPaperTestReport)
async def get_test_report(test_id: int, db: DBSession, user: CurrentUser):
    """获取测试报告（包含完整答题卡和题目详情）"""
    # 验证测试记录
    result = await db.execute(
        select(ExamPaperTest).where(ExamPaperTest.id == test_id, ExamPaperTest.user_id == user["id"])
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="测试记录不存在")

    # 获取考卷标题
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == test.exam_paper_id))
    paper = paper_result.scalar_one_or_none()

    # 获取答题记录
    answers_result = await db.execute(
        select(TestAnswerRecord)
        .options(selectinload(TestAnswerRecord.question))
        .where(TestAnswerRecord.test_id == test_id)
        .order_by(TestAnswerRecord.question_index)
    )
    answer_records = list(answers_result.scalars().all())

    # 构建答题卡数据
    answer_sheet = []
    for r in answer_records:
        question = r.question
        # 处理题目内容
        question_content = None
        question_options = None
        question_explanation = None
        question_title = None

        if question:
            question_title = question.title
            if question.content:
                question_content = question.content if isinstance(question.content, dict) else {"text": question.content}
            if question.options:
                question_options = question.options if isinstance(question.options, list) else []
            if question.explanation:
                question_explanation = question.explanation if isinstance(question.explanation, dict) else {"text": question.explanation}

        answer_sheet.append({
            "index": r.question_index,
            "question_id": r.question_id,
            "user_answer": r.user_answer,
            "correct_answer": r.correct_answer,
            "is_correct": r.is_correct,
            "question_title": question_title,
            "question_content": question_content,
            "question_options": question_options,
            "question_explanation": question_explanation
        })

    wrong_count = test.total_questions - (test.correct_count or 0)

    return ExamPaperTestReport(
        id=test.id,
        user_id=test.user_id,
        exam_paper_id=test.exam_paper_id,
        exam_paper_title=paper.title if paper else None,
        score=test.score or 0,
        correct_count=test.correct_count or 0,
        wrong_count=wrong_count,
        total_questions=test.total_questions,
        time_spent=test.time_spent or 0,
        started_at=test.started_at,
        finished_at=test.finished_at,
        status=test.status,
        answer_sheet=answer_sheet
    )


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
    practice_records = []  # 用于同步到PracticeRecord表
    wrong_question_ids = []  # 收集错题ID

    for i, q in enumerate(questions, 1):
        question_id = q.question_id
        correct_answer = q.question.answer
        user_answer = submit.answers.get(i)

        correct_answers_summary[i] = correct_answer

        # 未选择答案视为错误
        is_correct = bool(user_answer and user_answer.upper() == correct_answer.upper())
        if is_correct:
            correct_count += 1
        else:
            # 收集错题ID
            wrong_question_ids.append(question_id)

        # TestAnswerRecord（考卷测试专用）
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

        # PracticeRecord（通用答题记录，用于答题记录页面）
        practice_record = PracticeRecord(
            user_id=user["id"],
            question_id=question_id,
            user_answer=user_answer or "",
            is_correct=is_correct,
            time_spent=0  # 单题时间未知，使用0
        )
        practice_records.append(practice_record)

    score = int((correct_count / len(questions)) * 100) if questions else 0

    # 更新测试记录
    test.correct_count = correct_count
    test.score = score
    test.time_spent = submit.time_spent
    test.finished_at = datetime.utcnow()
    test.status = "completed"

    db.add_all(answer_records)
    db.add_all(practice_records)  # 同步保存到PracticeRecord表
    await db.commit()

    # 将错题加入错题本
    for question_id in wrong_question_ids:
        # 检查是否已存在
        existing = await db.execute(
            select(WrongQuestion)
            .where(WrongQuestion.user_id == user["id"])
            .where(WrongQuestion.question_id == question_id)
        )
        wrong_record = existing.scalar_one_or_none()
        if wrong_record:
            # 更新重试次数
            wrong_record.retry_count += 1
            wrong_record.last_retry_at = datetime.utcnow()
        else:
            # 创建新记录
            wrong_record = WrongQuestion(
                id=short_id(),
                user_id=user["id"],
                question_id=question_id
            )
            db.add(wrong_record)
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
async def list_exam_papers(db: DBSession, user: CurrentUser):
    """获取考卷列表，按用户难度等级过滤"""
    # 获取用户难度等级
    user_result = await db.execute(select(User).where(User.id == user["id"]))
    user_info = user_result.scalar_one_or_none()
    if not user_info:
        return []

    result = await db.execute(
        select(ExamPaper).where(ExamPaper.difficulty_level == user_info.difficulty_level)
    )
    return list(result.scalars().all())


@router.get("/recommended", response_model=list[ExamPaperResponse])
async def get_recommended_papers(db: DBSession, user: CurrentUser, limit: int = 2):
    """智能推荐考卷 - 根据薄弱专题推荐，排除已完成的考卷"""
    # 1. 获取用户信息
    user_result = await db.execute(select(User).where(User.id == user["id"]))
    user_info = user_result.scalar_one_or_none()
    if not user_info:
        return []

    # 使用用户难度等级（1-6），与用户答题水平挂钩
    user_difficulty = user_info.difficulty_level or 1

    # 2. 查询用户已完成的考卷（排除）
    completed_result = await db.execute(
        select(ExamPaperTest.exam_paper_id)
        .where(ExamPaperTest.user_id == user["id"])
        .where(ExamPaperTest.status == "completed")
    )
    completed_ids = [r for r in completed_result.scalars().all()]

    # 3. 查询用户薄弱专题（正确率最低）
    # 从practice_records统计各专题正确率
    topic_stats_result = await db.execute(
        select(
            Question.topic_id,
            func.count(PracticeRecord.id).label("total"),
            func.coalesce(func.sum(func.cast(PracticeRecord.is_correct, Integer)), 0).label("correct")
        )
        .join(Question, PracticeRecord.question_id == Question.id)
        .where(PracticeRecord.user_id == user["id"])
        .group_by(Question.topic_id)
        .order_by(func.coalesce(func.sum(func.cast(PracticeRecord.is_correct, Integer)), 0) / func.count(PracticeRecord.id))
    )
    topic_stats = topic_stats_result.all()

    # 构建薄弱专题列表（按正确率升序）
    weak_topics = []
    for s in topic_stats:
        if s.total > 0:
            rate = s.correct / s.total
            weak_topics.append({"topic_id": s.topic_id, "rate": rate})

    # 4. 查询符合条件的考卷（等级匹配 + 未完成）
    papers_result = await db.execute(
        select(ExamPaper)
        .where(ExamPaper.difficulty_level == user_difficulty)
        .where(ExamPaper.id.not_in(completed_ids) if completed_ids else True)
    )
    available_papers = list(papers_result.scalars().all())

    if not available_papers:
        # 如果没有未完成的考卷，返回空列表
        return []

    # 5. 计算每个考卷与薄弱专题的匹配度
    paper_scores = []
    for paper in available_papers:
        # 获取该考卷包含的专题
        paper_topics_result = await db.execute(
            select(func.distinct(Question.topic_id))
            .join(ExamPaperQuestion, Question.id == ExamPaperQuestion.question_id)
            .where(ExamPaperQuestion.exam_paper_id == paper.id)
        )
        paper_topic_ids = [t for t in paper_topics_result.scalars().all()]

        # 计算匹配分数：考卷包含的薄弱专题数量
        match_score = 0
        for weak in weak_topics:
            if weak["topic_id"] in paper_topic_ids:
                # 薄弱专题匹配加分（越薄弱加分越多）
                match_score += (1 - weak["rate"]) * 10

        paper_scores.append({
            "paper": paper,
            "score": match_score,
            "paper_type": paper.paper_type or "daily"
        })

    # 6. 排序：优先推荐匹配薄弱专题的考卷
    # 其次按类型排序：mock > topic > daily
    type_priority = {"mock": 3, "topic": 2, "daily": 1}

    paper_scores.sort(key=lambda x: (
        -x["score"],  # 匹配分数降序
        -type_priority.get(x["paper_type"], 1)  # 类型优先级降序
    ))

    # 7. 返回推荐考卷（最多limit个）
    recommended = paper_scores[:limit]
    return [ExamPaperResponse.model_validate(p["paper"]) for p in recommended]


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


@router.post("/{exam_paper_id}/submit", response_model=ExamPaperTestReport)
async def submit_exam_paper_direct(exam_paper_id: int, submit: ExamPaperTestSubmit, db: DBSession, user: CurrentUser):
    """直接提交考卷测试（无需预创建，一次性创建并完成）"""
    logger.info(f"提交考卷请求: user_id={user['id']}, exam_paper_id={exam_paper_id}, answers={submit.answers}, time_spent={submit.time_spent}")

    # 检查考卷是否存在
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = result.scalar_one_or_none()
    if not exam_paper:
        logger.warning(f"考卷不存在: exam_paper_id={exam_paper_id}")
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
        logger.info(f"删除旧测试记录: test_id={existing.id}")
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
    answer_records = []
    practice_records = []  # 用于同步到PracticeRecord表
    answer_sheet_data = []  # 用于返回答题卡数据
    wrong_question_ids = []  # 收集错题ID

    for i, q in enumerate(questions, 1):
        question_id = q.question_id
        question = q.question
        correct_answer = question.answer
        user_answer = submit.answers.get(i)

        # 未选择答案视为错误
        is_correct = bool(user_answer and user_answer.upper() == correct_answer.upper())
        if is_correct:
            correct_count += 1
        else:
            # 收集错题ID
            wrong_question_ids.append(question_id)

        # 处理题目内容
        question_content = None
        question_options = None
        question_explanation = None
        if question.content:
            question_content = question.content if isinstance(question.content, dict) else {"text": question.content}
        if question.options:
            question_options = question.options if isinstance(question.options, list) else []
        if question.explanation:
            question_explanation = question.explanation if isinstance(question.explanation, dict) else {"text": question.explanation}

        # 答题卡数据
        answer_sheet_data.append({
            "index": i,
            "question_id": question_id,
            "user_answer": user_answer or "",
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "question_title": question.title,
            "question_content": question_content,
            "question_options": question_options,
            "question_explanation": question_explanation
        })

        # TestAnswerRecord（考卷测试专用）
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

        # PracticeRecord（通用答题记录，用于答题记录页面）
        practice_record = PracticeRecord(
            user_id=user["id"],
            question_id=question_id,
            user_answer=user_answer or "",
            is_correct=is_correct,
            time_spent=0  # 单题时间未知，使用0
        )
        practice_records.append(practice_record)

    score = int((correct_count / len(questions)) * 100) if questions else 0
    wrong_count = len(questions) - correct_count
    logger.info(f"计算得分: correct_count={correct_count}, wrong_count={wrong_count}, score={score}, wrong_question_ids={wrong_question_ids}")

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
    logger.info(f"创建测试记录: test_id={test.id}")

    # 更新答题记录的 test_id
    for record in answer_records:
        record.test_id = test.id

    db.add_all(answer_records)
    db.add_all(practice_records)  # 同步保存到PracticeRecord表
    await db.commit()
    logger.info(f"保存答题记录: {len(answer_records)}条TestAnswerRecord, {len(practice_records)}条PracticeRecord")

    # 将错题加入错题本
    for question_id in wrong_question_ids:
        # 检查是否已存在
        existing_wrong = await db.execute(
            select(WrongQuestion)
            .where(WrongQuestion.user_id == user["id"])
            .where(WrongQuestion.question_id == question_id)
        )
        wrong_record = existing_wrong.scalar_one_or_none()
        if wrong_record:
            # 更新重试次数
            wrong_record.retry_count += 1
            wrong_record.last_retry_at = datetime.utcnow()
            logger.info(f"更新错题记录: question_id={question_id}, retry_count={wrong_record.retry_count}")
        else:
            # 创建新记录
            wrong_record = WrongQuestion(
                id=short_id(),
                user_id=user["id"],
                question_id=question_id
            )
            db.add(wrong_record)
            logger.info(f"创建错题记录: question_id={question_id}")
    await db.commit()

    logger.info(f"提交考卷完成: test_id={test.id}, score={score}")

    return ExamPaperTestReport(
        id=test.id,
        user_id=test.user_id,
        exam_paper_id=test.exam_paper_id,
        exam_paper_title=exam_paper.title,
        score=score,
        correct_count=correct_count,
        wrong_count=wrong_count,
        total_questions=len(questions),
        time_spent=submit.time_spent,
        started_at=now,
        finished_at=now,
        status="completed",
        answer_sheet=answer_sheet_data
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