"""
ExamPaper API for miniapp - 用户端考卷接口
"""
import logging
import os
import random
from datetime import datetime
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, delete, insert, and_, Integer
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, CurrentUser, CurrentUserOptional
from app.models.exam_paper import ExamPaper, ExamPaperQuestion
from app.models.exam_paper_test import ExamPaperTest
from app.models.exam_paper_test_answer import TestAnswerRecord
from app.models.question import Question
from app.models.topic import Topic
from app.models.favorite import WrongQuestion
from app.models.practice_record import PracticeRecord
from app.models.user import User
from app.schemas.exam_paper import (
    ExamPaperResponse, ExamPaperWithQuestions, ExamPaperListResponse,
    ExamPaperTestStart, ExamPaperTestAnswer, ExamPaperTestSubmit,
    ExamPaperTestResponse, ExamPaperTestDetail, ExamPaperTestList,
    ExamPaperTestAnswerResponse, UserWrongQuestion, ExamPaperTestReport,
    GeneratePaperRequest, GeneratePaperResponse,
    GeneratePdfResponse, DeletePaperResponse,
)
from app.utils.id_generator import short_id

from app.utils.pdf import render_exam_paper_pdf_stream

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

@router.get("", response_model=ExamPaperListResponse)
async def list_exam_papers(
    db: DBSession,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    paper_type: str | None = Query(default=None),
):
    """获取考卷列表（分页，支持按类型筛选），附带用户作答状态"""
    # 获取用户难度等级
    user_result = await db.execute(select(User).where(User.id == user["id"]))
    user_info = user_result.scalar_one_or_none()
    if not user_info:
        return ExamPaperListResponse(total=0, page=page, page_size=page_size, items=[])

    # 构建查询条件
    conditions = [
        ExamPaper.difficulty_level == user_info.difficulty_level,
        ExamPaper.status == "published",
        ExamPaper.user_id == 100000000000,
    ]
    if paper_type:
        conditions.append(ExamPaper.paper_type == paper_type)

    # 查询总数
    count_result = await db.execute(
        select(func.count()).select_from(ExamPaper).where(and_(*conditions))
    )
    total = count_result.scalar() or 0

    # 分页查询
    offset = (page - 1) * page_size
    result = await db.execute(
        select(ExamPaper)
        .where(and_(*conditions))
        .order_by(ExamPaper.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    papers = list(result.scalars().all())

    if not papers:
        return ExamPaperListResponse(total=total, page=page, page_size=page_size, items=[])

    # 查询用户对这些考卷的测试记录
    paper_ids = [p.id for p in papers]
    tests_result = await db.execute(
        select(ExamPaperTest.exam_paper_id, ExamPaperTest.score, ExamPaperTest.status)
        .where(ExamPaperTest.user_id == user["id"])
        .where(ExamPaperTest.exam_paper_id.in_(paper_ids))
    )
    user_tests = tests_result.all()

    # 构建 paper_id -> 测试记录 的映射
    test_map: dict[int, tuple[int | None, str]] = {}
    for t in user_tests:
        existing = test_map.get(t.exam_paper_id)
        if existing and existing[1] == "completed":
            continue
        if t.status == "completed":
            test_map[t.exam_paper_id] = (t.score, t.status)

    # 组装响应
    responses = []
    for paper in papers:
        test_info = test_map.get(paper.id)
        is_new_val = bool(paper.is_new) if paper.is_new is not None else False
        logger.info(f"Paper {paper.id}: DB is_new={paper.is_new!r}, computed={is_new_val}")
        responses.append(ExamPaperResponse(
            id=paper.id,
            title=paper.title,
            difficulty_level=paper.difficulty_level,
            total_questions=paper.total_questions,
            description=paper.description,
            paper_type=paper.paper_type,
            file_path=paper.file_path,
            is_new=is_new_val,
            user_completed=test_info is not None,
            user_score=test_info[0] if test_info else None,
            created_at=paper.created_at,
            updated_at=paper.updated_at,
        ))

    return ExamPaperListResponse(total=total, page=page, page_size=page_size, items=responses)


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

    # 4. 查询符合条件的考卷（已上架 + 等级匹配 + 未完成）
    papers_result = await db.execute(
        select(ExamPaper)
        .where(ExamPaper.status == "published")
        .where(ExamPaper.difficulty_level == user_difficulty)
        .where(ExamPaper.id.not_in(completed_ids) if completed_ids else True)
        .order_by(ExamPaper.created_at.desc())
    )
    available_papers = list(papers_result.scalars().all())

    if not available_papers:
        # 如果没有未完成的考卷，尝试获取所有等级最新考卷
        fallback_result = await db.execute(
            select(ExamPaper)
            .where(ExamPaper.status == "published")
            .order_by(ExamPaper.created_at.desc())
            .limit(limit)
        )
        final_papers = list(fallback_result.scalars().all())
    else:
        paper_scores = []
        for paper in available_papers:
            paper_topics_result = await db.execute(
                select(func.distinct(Question.topic_id))
                .join(ExamPaperQuestion, Question.id == ExamPaperQuestion.question_id)
                .where(ExamPaperQuestion.exam_paper_id == paper.id)
            )
            paper_topic_ids = [t for t in paper_topics_result.scalars().all()]

            match_score = 0
            for weak in weak_topics:
                if weak["topic_id"] in paper_topic_ids:
                    match_score += (1 - weak["rate"]) * 10

            paper_scores.append({
                "paper": paper,
                "score": match_score,
                "paper_type": paper.paper_type or "daily"
            })

        type_priority = {"mock": 3, "topic": 2, "daily": 1, "past": 4}
        paper_scores.sort(key=lambda x: (
            -x["score"],
            -type_priority.get(x["paper_type"], 1),
            -(x["paper"].created_at.timestamp() if x["paper"].created_at else 0)
        ))

        final_papers = [p["paper"] for p in paper_scores[:limit]]

    # 查询用户对这些考卷的测试记录，标记已作答状态
    paper_ids = [p.id for p in final_papers]
    tests_result = await db.execute(
        select(ExamPaperTest.exam_paper_id, ExamPaperTest.score, ExamPaperTest.status)
        .where(ExamPaperTest.user_id == user["id"])
        .where(ExamPaperTest.exam_paper_id.in_(paper_ids))
    )
    test_map: dict[int, int | None] = {}
    for t in tests_result.all():
        existing = test_map.get(t.exam_paper_id)
        if existing is not None:
            continue
        if t.status == "completed":
            test_map[t.exam_paper_id] = t.score

    return [
        ExamPaperResponse(
            id=p.id,
            title=p.title,
            difficulty_level=p.difficulty_level,
            total_questions=p.total_questions,
            description=p.description,
            paper_type=p.paper_type,
            file_path=p.file_path,
            is_new=p.is_new,
            user_completed=p.id in test_map,
            user_score=test_map.get(p.id),
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in final_papers
    ]


@router.post("/generate", response_model=GeneratePaperResponse)
async def generate_exam_paper(req: GeneratePaperRequest, db: DBSession, user: CurrentUser):
    """用户生成考卷"""
    # 1. 确定专题列表
    topic_ids = []

    if req.mode == "smart":
        # 智能模式：分析用户薄弱专题
        stats_result = await db.execute(
            select(
                Question.topic_id,
                func.count(PracticeRecord.id).label("total"),
                func.sum(func.cast(PracticeRecord.is_correct, Integer)).label("correct")
            )
            .join(Question, PracticeRecord.question_id == Question.id)
            .where(PracticeRecord.user_id == user["id"])
            .group_by(Question.topic_id)
            .order_by(
                func.sum(func.cast(PracticeRecord.is_correct, Integer)) / func.count(PracticeRecord.id)
            )
        )
        stats = stats_result.all()

        if stats:
            # 取正确率最低的 3 个专题
            for s in stats[:3]:
                topic_ids.append(s.topic_id)
        else:
            # 新用户：随机取有题目的专题
            topics_result = await db.execute(
                select(Question.topic_id)
                .where(Question.status == "published")
                .distinct()
                .limit(3)
            )
            topic_ids = [t for t in topics_result.scalars().all()]
    else:
        # 手动模式
        if not req.topic_ids:
            raise HTTPException(status_code=400, detail="手动模式请选择专题")
        topic_ids = req.topic_ids

    # 确定标题（用户自定义优先）
    if req.title:
        title = req.title.strip()
    elif req.mode == "smart":
        title = "智能推荐卷"
    else:
        first_topic = await db.execute(select(Topic.title).where(Topic.id == topic_ids[0]))
        first_title = first_topic.scalar_one_or_none() or ""
        suffix = f"+等" if len(topic_ids) > 1 else ""
        title = f"自定义卷 - {first_title}{suffix}"

    if not topic_ids:
        raise HTTPException(status_code=400, detail="没有可用的专题")

    # 2. 查询符合条件的题目
    questions_query = select(Question.id).where(
        Question.status == "published",
        Question.difficulty_level == req.difficulty_level,
        Question.topic_id.in_(topic_ids)
    )
    questions_result = await db.execute(questions_query)
    all_question_ids = list(questions_result.scalars().all())

    if not all_question_ids:
        raise HTTPException(status_code=400, detail="没有符合条件的题目")

    # 3. 随机选取
    random.shuffle(all_question_ids)
    selected_ids = all_question_ids[:min(req.question_count, len(all_question_ids))]

    # 4. 创建 ExamPaper
    paper = ExamPaper(
        title=title,
        difficulty_level=req.difficulty_level,
        total_questions=len(selected_ids),
        paper_type="custom",
        status="published",
        user_id=user["id"],
        generation_config={
            "mode": req.mode,
            "topic_ids": topic_ids,
            "difficulty_level": req.difficulty_level,
            "question_count": req.question_count,
        }
    )
    db.add(paper)
    await db.flush()

    # 5. 创建 ExamPaperQuestion 关联
    for i, qid in enumerate(selected_ids, 1):
        db.add(ExamPaperQuestion(
            exam_paper_id=paper.id,
            question_id=qid,
            sort=i
        ))

    await db.commit()
    await db.refresh(paper)

    return GeneratePaperResponse(
        exam_paper_id=paper.id,
        title=paper.title,
        total_questions=paper.total_questions
    )


@router.get("/my", response_model=ExamPaperListResponse)
async def get_my_papers(
    db: DBSession,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """获取用户生成的考卷列表"""
    conditions = [ExamPaper.user_id == user["id"]]

    count_result = await db.execute(
        select(func.count()).select_from(ExamPaper).where(and_(*conditions))
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(ExamPaper)
        .where(and_(*conditions))
        .order_by(ExamPaper.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    papers = list(result.scalars().all())

    # 查询用户对这些考卷的测试记录
    paper_ids = [p.id for p in papers]
    test_map = {}
    if paper_ids:
        tests_result = await db.execute(
            select(ExamPaperTest.exam_paper_id, ExamPaperTest.score, ExamPaperTest.status)
            .where(ExamPaperTest.user_id == user["id"])
            .where(ExamPaperTest.exam_paper_id.in_(paper_ids))
        )
        for t in tests_result.all():
            if t.exam_paper_id not in test_map and t.status == "completed":
                test_map[t.exam_paper_id] = (t.score, t.status)

    items = [
        ExamPaperResponse(
            id=p.id, title=p.title, difficulty_level=p.difficulty_level,
            total_questions=p.total_questions, description=p.description,
            paper_type=p.paper_type, file_path=p.file_path,
            is_new=False, status=p.status,
            user_id=p.user_id, generation_config=p.generation_config,
            user_completed=p.id in test_map,
            user_score=test_map[p.id][0] if p.id in test_map else None,
            created_at=p.created_at, updated_at=p.updated_at,
        )
        for p in papers
    ]

    return ExamPaperListResponse(total=total, page=page, page_size=page_size, items=items)


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


@router.get("/{exam_paper_id}/export-pdf")
async def export_exam_paper_pdf(exam_paper_id: int, db: DBSession, user: CurrentUserOptional):
    """导出考卷为 PDF 文件"""
    # 查询考卷
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")

    # 加载题目
    questions_result = await db.execute(
        select(ExamPaperQuestion)
        .options(selectinload(ExamPaperQuestion.question))
        .where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
        .order_by(ExamPaperQuestion.sort)
    )
    ep_questions = list(questions_result.scalars().all())

    if not ep_questions:
        raise HTTPException(status_code=400, detail="考卷无题目")

    # 组装题目数据
    questions_data = []
    for eq in ep_questions:
        q = eq.question
        questions_data.append({
            "content": q.content,
            "options": q.options,
            "explanation": q.explanation,
            "answer": q.answer,
        })

    # 生成 PDF
    pdf_stream = render_exam_paper_pdf_stream(
        title=exam_paper.title,
        difficulty_level=exam_paper.difficulty_level,
        description=exam_paper.description,
        questions=questions_data,
    )

    filename = f"{exam_paper.title}.pdf"
    encoded_filename = quote(filename)
    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@router.get("/{exam_paper_id}/download-pdf")
async def download_exam_paper_pdf(exam_paper_id: int, db: DBSession, user: CurrentUserOptional):
    """下载已生成的考卷 PDF（从 file_path 读取）"""
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")

    if not exam_paper.file_path or not os.path.exists(exam_paper.file_path):
        raise HTTPException(status_code=404, detail="PDF 文件不存在，请先生成 PDF")

    filename = quote(f"{exam_paper.title}.pdf")
    return StreamingResponse(
        open(exam_paper.file_path, "rb"),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.post("/{exam_paper_id}/generate-pdf", response_model=GeneratePdfResponse)
async def generate_exam_paper_pdf(exam_paper_id: int, db: DBSession, user: CurrentUser):
    """生成考卷 PDF 并保存到文件"""
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")
    if exam_paper.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="只能操作自己的考卷")

    # 已存在则直接返回
    if exam_paper.file_path and os.path.exists(exam_paper.file_path):
        return GeneratePdfResponse(exam_paper_id=exam_paper.id, file_path=exam_paper.file_path)

    # 查询题目
    questions_result = await db.execute(
        select(ExamPaperQuestion).where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
        .order_by(ExamPaperQuestion.sort)
    )
    ep_questions = list(questions_result.scalars().all())
    if not ep_questions:
        raise HTTPException(status_code=400, detail="考卷无题目")

    ep_q_ids = [eq.question_id for eq in ep_questions]
    q_result = await db.execute(select(Question).where(Question.id.in_(ep_q_ids)))
    q_map = {q.id: q for q in q_result.scalars().all()}

    questions_data = []
    for eq_id in ep_q_ids:
        q = q_map.get(eq_id)
        if q:
            questions_data.append({
                "content": q.content,
                "options": q.options,
                "explanation": q.explanation,
                "answer": q.answer,
            })

    if not questions_data:
        raise HTTPException(status_code=400, detail="考卷无有效题目")

    # 生成 PDF
    from app.core.config import settings
    pdf_stream = render_exam_paper_pdf_stream(
        title=exam_paper.title,
        difficulty_level=exam_paper.difficulty_level,
        description=exam_paper.description,
        questions=questions_data,
    )

    # 保存到文件
    os.makedirs(settings.pdf_output_dir, exist_ok=True)
    filename = f"paper_{exam_paper_id}_{short_id()}.pdf"
    file_path = os.path.join(settings.pdf_output_dir, filename)
    pdf_bytes = b"".join(pdf_stream)
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    exam_paper.file_path = file_path
    await db.flush()

    return GeneratePdfResponse(exam_paper_id=exam_paper.id, file_path=file_path)


@router.delete("/{exam_paper_id}", response_model=DeletePaperResponse)
async def delete_exam_paper(exam_paper_id: int, db: DBSession, user: CurrentUser):
    """删除用户生成的考卷"""
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")
    if exam_paper.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="只能删除自己的考卷")
    if exam_paper.paper_type != "custom":
        raise HTTPException(status_code=400, detail="只能删除用户生成的考卷")

    # 删除 PDF 文件
    if exam_paper.file_path and os.path.exists(exam_paper.file_path):
        try:
            os.remove(exam_paper.file_path)
        except OSError:
            pass

    # 删除关联的考试记录和答案
    test_ids_result = await db.execute(
        select(ExamPaperTest.id).where(ExamPaperTest.exam_paper_id == exam_paper_id)
    )
    test_ids = [t for t in test_ids_result.scalars().all()]
    if test_ids:
        await db.execute(delete(TestAnswerRecord).where(TestAnswerRecord.test_id.in_(test_ids)))
        await db.execute(delete(ExamPaperTest).where(ExamPaperTest.exam_paper_id == exam_paper_id))

    # 删除题目关联
    await db.execute(
        delete(ExamPaperQuestion).where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
    )

    # 删除考卷
    await db.execute(delete(ExamPaper).where(ExamPaper.id == exam_paper_id))
    await db.commit()

    return DeletePaperResponse(ok=True)


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