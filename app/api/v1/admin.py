"""
Admin management API - 用户、专题、题目、考卷管理
"""
import logging
import os
import datetime
import io
import uuid
import zipfile
from urllib.parse import quote

import cv2
import numpy as np

from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import select, func, delete, text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.api.deps import DBSession, AdminUser
from app.core.config import settings
from app.db.session import engine
from app.models.user import User
from app.models.topic import Topic
from app.models.question import Question
from app.models.exam_paper import ExamPaper, ExamPaperQuestion
from app.models.practice_record import PracticeRecord
from app.models.user_download import UserDownloadRecord
from app.schemas.user import UserResponse, UserTierUpdate
from app.schemas.topic import TopicResponse, TopicCreate, TopicUpdate
from app.schemas.question import QuestionResponse, QuestionCreate, QuestionUpdate, BatchImportResponse
from app.services.question_batch_import import batch_import
from app.schemas.exam_paper import (
    ExamPaperResponse, ExamPaperCreate, ExamPaperUpdate, ExamPaperWithQuestions,
    ExamPaperQuestionCreate, ExamPaperQuestionUpdate, ExamPaperQuestionResponse,
    UserDownloadRecordResponse, UserDownloadRecordListResponse,
)
from app.utils.pdf import render_exam_paper_pdf_stream

logger = logging.getLogger(__name__)

PDF_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "storage", "exam_papers")
os.makedirs(PDF_STORAGE_DIR, exist_ok=True)

router = APIRouter()


# ============ 用户管理 ============

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    admin: AdminUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    grade: str | None = None,
    difficulty_level: int | None = None,
    daily_goal: int | None = None,
    user_tier: str | None = None,
):
    """获取用户列表"""
    query = select(User).options(
        noload(User.practice_records),
        noload(User.favorites),
        noload(User.wrong_questions)
    )
    if keyword:
        query = query.where(User.nickname.ilike(f"%{keyword}%"))
    if grade:
        query = query.where(User.grade == grade)
    if difficulty_level:
        query = query.where(User.difficulty_level == difficulty_level)
    if daily_goal:
        query = query.where(User.daily_goal == daily_goal)
    if user_tier:
        query = query.where(User.user_tier == user_tier)
    query = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_detail(user_id: int, admin: AdminUser, db: DBSession):
    """获取用户详情"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/users/{user_id}/tier", response_model=UserResponse)
async def update_user_tier(user_id: int, data: UserTierUpdate, admin: AdminUser, db: DBSession):
    """设置用户等级（free/pro）和 pro 到期时间"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.user_tier = data.user_tier
    user.tier_expires_at = data.tier_expires_at
    await db.commit()
    await db.refresh(user)
    return user


# ============ 用户下载记录 ============

@router.get("/pdf-downloads", response_model=UserDownloadRecordListResponse)
async def list_user_downloads(
    admin: AdminUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: int | None = None,
    exam_paper_id: int | None = None,
    keyword: str | None = None,
):
    """获取PDF下载记录列表"""
    query = select(UserDownloadRecord)

    if user_id:
        query = query.where(UserDownloadRecord.user_id == user_id)
    if exam_paper_id:
        query = query.where(UserDownloadRecord.exam_paper_id == exam_paper_id)
    if keyword:
        query = query.where(UserDownloadRecord.exam_paper_title.ilike(f"%{keyword}%"))

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar() or 0

    query = query.order_by(UserDownloadRecord.downloaded_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return UserDownloadRecordListResponse(total=total, items=items)


# ============ 专题管理 ============

@router.get("/topics", response_model=list[TopicResponse])
async def list_topics_admin(admin: AdminUser, db: DBSession):
    """获取专题列表"""
    result = await db.execute(
        select(Topic).options(
            noload(Topic.questions),
        )
    )
    return list(result.scalars().all())


@router.post("/topics", response_model=TopicResponse)
async def create_topic(data: TopicCreate, admin: AdminUser, db: DBSession):
    """创建专题"""
    topic = Topic(**data.model_dump())
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic


@router.put("/topics/{topic_id}", response_model=TopicResponse)
async def update_topic(topic_id: int, data: TopicUpdate, admin: AdminUser, db: DBSession):
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
async def delete_topic(topic_id: int, admin: AdminUser, db: DBSession):
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
    admin: AdminUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    topic_id: int | None = None,
    difficulty_level: int | None = None,
    source_year: int | None = None,
    status: str | None = None,
    content: str | None = None,
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
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
    if difficulty_level:
        query = query.where(Question.difficulty_level == difficulty_level)
    if source_year:
        query = query.where(Question.source_year == source_year)
    if status:
        query = query.where(Question.status == status)
    if content:
        query = query.where(Question.content["text"].as_string().like(f"%{content}%"))
    order_by = Question.id.asc() if sort_order == "asc" else Question.id.desc()
    query = query.order_by(order_by).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/questions", response_model=QuestionResponse)
async def create_question(data: QuestionCreate, admin: AdminUser, db: DBSession):
    """创建题目"""
    question = Question(**data.model_dump())
    db.add(question)
    await db.commit()
    await db.refresh(question)
    logger.info(f"创建题目: id={question.id}, topic_id={data.topic_id}, difficulty={data.difficulty_level}, answer={data.answer}")
    return question


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(question_id: int, data: QuestionUpdate, admin: AdminUser, db: DBSession):
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
    logger.info(f"更新题目: id={question_id}, fields={set(data.model_dump(exclude_unset=True).keys())}")
    return question


@router.delete("/questions/{question_id}")
async def delete_question(question_id: int, admin: AdminUser, db: DBSession):
    """删除题目"""
    result = await db.execute(
        select(Question).options(
            noload(Question.topic),
            noload(Question.practice_records),
            noload(Question.favorites),
            noload(Question.wrong_questions),
            noload(Question.likes),
        ).where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    await db.delete(question)
    await db.commit()
    logger.info(f"删除题目: id={question_id}")
    return {"message": "删除成功"}


@router.post("/questions/batch-delete")
async def batch_delete_questions(ids: list[int], admin: AdminUser, db: DBSession):
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
                noload(Question.wrong_questions),
                noload(Question.likes),
            ).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        if question:
            await db.delete(question)
            deleted_count += 1

    await db.commit()
    logger.info(f"批量删除题目: ids={ids}, deleted_count={deleted_count}")
    return {"message": f"成功删除 {deleted_count} 道题目", "deleted_count": deleted_count}


@router.post("/questions/batch-import", response_model=BatchImportResponse)
async def batch_import_questions(
    admin: AdminUser,
    db: DBSession,
    excel: UploadFile = File(...),
    zip: UploadFile | None = File(None),
):
    """批量导入题目（Excel + 可选 ZIP 图片包）"""
    if not excel.filename or not excel.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="文件格式错误，仅支持 .xlsx 格式")

    excel_bytes = await excel.read()
    zip_bytes = None
    if zip and zip.filename:
        if not zip.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="图片包仅支持 .zip 格式")
        zip_bytes = await zip.read()

    result = await batch_import(db, excel_bytes, zip_bytes)
    return BatchImportResponse(data=result.to_dict())


@router.get("/questions/batch-import-template")
async def download_batch_import_template(admin: AdminUser):
    """下载批量导入 Excel 模板"""
    template_path = "app/static/templates/batch_import_template.xlsx"
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="模板文件不存在")
    return FileResponse(
        template_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="batch_import_template.xlsx",
    )


@router.post("/questions/batch-publish")
async def batch_publish_questions(ids: list[int], admin: AdminUser, db: DBSession):
    """批量上架题目"""
    if not ids:
        raise HTTPException(status_code=400, detail="请提供要上架的题目ID")
    result = await db.execute(
        select(Question).where(Question.id.in_(ids)).options(
            noload(Question.topic), noload(Question.practice_records),
            noload(Question.favorites), noload(Question.wrong_questions)
        )
    )
    questions = result.scalars().all()
    updated = 0
    for q in questions:
        q.status = "published"
        updated += 1
    await db.commit()
    logger.info(f"批量上架题目: ids={ids}, updated={updated}")
    return {"message": f"成功上架 {updated} 道题目", "updated_count": updated}


@router.post("/questions/batch-unpublish")
async def batch_unpublish_questions(ids: list[int], admin: AdminUser, db: DBSession):
    """批量下架题目"""
    if not ids:
        raise HTTPException(status_code=400, detail="请提供要下架的题目ID")
    result = await db.execute(
        select(Question).where(Question.id.in_(ids)).options(
            noload(Question.topic), noload(Question.practice_records),
            noload(Question.favorites), noload(Question.wrong_questions)
        )
    )
    questions = result.scalars().all()
    updated = 0
    for q in questions:
        q.status = "unpublished"
        updated += 1
    await db.commit()
    logger.info(f"批量下架题目: ids={ids}, updated={updated}")
    return {"message": f"成功下架 {updated} 道题目", "updated_count": updated}


@router.post("/questions/{question_id}/publish")
async def publish_question(question_id: int, admin: AdminUser, db: DBSession):
    """上架题目"""
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
    question.status = "published"
    await db.commit()
    logger.info(f"上架题目: id={question_id}")
    return {"message": "上架成功"}


@router.post("/questions/{question_id}/unpublish")
async def unpublish_question(question_id: int, admin: AdminUser, db: DBSession):
    """下架题目"""
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
    question.status = "unpublished"
    await db.commit()
    logger.info(f"下架题目: id={question_id}")
    return {"message": "下架成功"}


@router.get("/questions/count")
async def get_questions_count(admin: AdminUser, db: DBSession, topic_id: int | None = None):
    """获取题目总数"""
    query = select(func.count(Question.id))
    if topic_id:
        query = query.where(Question.topic_id == topic_id)
    result = await db.execute(query)
    return {"total": result.scalar()}


# ============ 统计数据 ============

@router.get("/stats")
async def get_dashboard_stats(admin: AdminUser, db: DBSession):
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
async def get_users_count(admin: AdminUser, db: DBSession):
    """获取用户总数"""
    result = await db.execute(select(func.count(User.id)))
    return {"total": result.scalar()}


@router.get("/stats/questions")
async def get_questions_stats(
    admin: AdminUser,
    db: DBSession,
    topic_id: int | None = None,
    difficulty_level: int | None = None,
    source_year: int | None = None,
    status: str | None = None,
    content: str | None = None,
):
    """获取题目统计"""
    query = select(func.count(Question.id))
    if topic_id:
        query = query.where(Question.topic_id == topic_id)
    if difficulty_level:
        query = query.where(Question.difficulty_level == difficulty_level)
    if source_year:
        query = query.where(Question.source_year == source_year)
    if status:
        query = query.where(Question.status == status)
    if content:
        query = query.where(Question.content["text"].as_string().like(f"%{content}%"))
    result = await db.execute(query)
    return {"total": result.scalar()}


# ============ 考卷管理 ============

@router.get("/exam-papers", response_model=list[ExamPaperResponse])
async def list_exam_papers(
    admin: AdminUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    difficulty_level: int | None = None,
    paper_type: str | None = None,
    title: str | None = None
):
    """获取考卷列表"""
    query = select(ExamPaper)
    if difficulty_level:
        query = query.where(ExamPaper.difficulty_level == difficulty_level)
    if paper_type:
        query = query.where(ExamPaper.paper_type == paper_type)
    if title:
        query = query.where(ExamPaper.title.like(f"%{title}%"))
    query = query.order_by(ExamPaper.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/exam-papers", response_model=ExamPaperResponse)
async def create_exam_paper(data: ExamPaperCreate, admin: AdminUser, db: DBSession):
    """创建考卷"""
    create_data = data.model_dump(exclude_none=True)
    exam_paper = ExamPaper(**create_data)
    exam_paper.user_id = 100000000000
    db.add(exam_paper)
    await db.commit()
    await db.refresh(exam_paper)
    return exam_paper


@router.get("/exam-papers/{exam_paper_id}", response_model=ExamPaperWithQuestions)
async def get_exam_paper_detail(exam_paper_id: int, admin: AdminUser, db: DBSession):
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
async def update_exam_paper(exam_paper_id: int, data: ExamPaperUpdate, admin: AdminUser, db: DBSession):
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
async def delete_exam_paper(exam_paper_id: int, admin: AdminUser, db: DBSession):
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


@router.post("/exam-papers/{exam_paper_id}/export-pdf")
async def export_admin_exam_paper_pdf(exam_paper_id: int, admin: AdminUser, db: DBSession):
    """生成并导出考卷 PDF，保存到本地存储"""
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

    # 保存到本地存储
    pdf_path = os.path.join(PDF_STORAGE_DIR, f"{exam_paper_id}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_stream.getvalue())

    # 更新数据库 file_path
    exam_paper.file_path = pdf_path
    await db.commit()
    logger.info(f"导出考卷PDF: exam_paper_id={exam_paper_id}, title={exam_paper.title}, questions={len(questions_data)}")

    # 返回 PDF 流
    pdf_stream.seek(0)
    filename = quote(f"{exam_paper.title}.pdf")
    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/exam-papers/{exam_paper_id}/download-pdf")
async def download_exam_paper_pdf(exam_paper_id: int, admin: AdminUser, db: DBSession):
    """下载已生成的考卷 PDF"""
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


# ============ 考卷题目管理 ============

@router.get("/exam-papers/{exam_paper_id}/questions", response_model=list[ExamPaperQuestionResponse])
async def list_exam_paper_questions(exam_paper_id: int, admin: AdminUser, db: DBSession):
    """获取考卷题目列表"""
    result = await db.execute(
        select(ExamPaperQuestion)
        .options(selectinload(ExamPaperQuestion.question))
        .where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
        .order_by(ExamPaperQuestion.sort)
    )
    return list(result.scalars().all())


@router.post("/exam-papers/{exam_paper_id}/questions", response_model=ExamPaperQuestionResponse)
async def add_question_to_exam_paper(exam_paper_id: int, data: ExamPaperQuestionCreate, admin: AdminUser, db: DBSession):
    """添加题目到考卷"""
    # 检查考卷是否存在
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = paper_result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")

    # 检查题目是否存在且已发布
    question_result = await db.execute(select(Question).where(Question.id == data.question_id))
    question = question_result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    if question.status != "published":
        raise HTTPException(status_code=400, detail="只能添加已发布的题目")

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


@router.post("/exam-papers/{exam_paper_id}/questions/random")
async def add_random_questions_to_exam_paper(
    exam_paper_id: int,
    admin: AdminUser,
    db: DBSession,
    topic_ids: list[int] | None = Body(None, embed=True)
):
    """随机添加题目到考卷（按难度等级匹配，补全剩余题目数量）"""
    # 检查考卷是否存在
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = paper_result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")

    # 计算可添加数量
    count_result = await db.execute(
        select(func.count(ExamPaperQuestion.id)).where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
    )
    current_count = count_result.scalar() or 0
    remaining = exam_paper.total_questions - current_count
    if remaining <= 0:
        raise HTTPException(status_code=400, detail=f"考卷题目已满（{exam_paper.total_questions}题）")

    # 查询已添加的题目 ID
    existing_result = await db.execute(
        select(ExamPaperQuestion.question_id).where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
    )
    existing_ids = {row[0] for row in existing_result.all()}

    # 随机选取匹配难度等级的已发布题目（排除已添加的）
    query = (
        select(Question.id)
        .where(Question.status == "published")
        .where(Question.difficulty_level == exam_paper.difficulty_level)
        .order_by(func.rand())
        .limit(remaining)
    )
    if existing_ids:
        query = query.where(Question.id.notin_(existing_ids))
    if topic_ids:
        query = query.where(Question.topic_id.in_(topic_ids))

    random_result = await db.execute(query)
    question_ids = [row[0] for row in random_result.all()]

    if not question_ids:
        raise HTTPException(status_code=400, detail="题库中没有更多匹配难度等级的题目")

    # 获取当前最大排序号
    max_sort_result = await db.execute(
        select(func.max(ExamPaperQuestion.sort)).where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
    )
    max_sort = max_sort_result.scalar() or 0

    # 批量添加
    added = []
    for i, qid in enumerate(question_ids):
        epq = ExamPaperQuestion(
            exam_paper_id=exam_paper_id,
            question_id=qid,
            sort=max_sort + i + 1
        )
        db.add(epq)
        added.append({"question_id": qid, "sort": max_sort + i + 1})

    await db.commit()

    return {
        "message": f"已随机添加 {len(added)} 道题目",
        "added_count": len(added),
        "questions": added
    }


@router.delete("/exam-papers/{exam_paper_id}/questions")
async def clear_exam_paper_questions(exam_paper_id: int, admin: AdminUser, db: DBSession):
    """清空考卷所有题目"""
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_paper_id))
    exam_paper = paper_result.scalar_one_or_none()
    if not exam_paper:
        raise HTTPException(status_code=404, detail="考卷不存在")

    await db.execute(
        delete(ExamPaperQuestion).where(ExamPaperQuestion.exam_paper_id == exam_paper_id)
    )
    await db.commit()
    return {"message": "已清空所有题目"}


@router.delete("/exam-papers/{exam_paper_id}/questions/{question_id}")
async def remove_question_from_exam_paper(exam_paper_id: int, question_id: int, admin: AdminUser, db: DBSession):
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
async def update_exam_paper_questions_sort(exam_paper_id: int, sorts: list[dict], admin: AdminUser, db: DBSession):
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


@router.get("/config")
async def get_admin_config(admin: AdminUser):
    """获取管理后台配置"""
    return {
        "server_host": settings.server_host,
    }


# ============ 数据备份 ============

BACKUP_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "storage", "backups")
os.makedirs(BACKUP_STORAGE_DIR, exist_ok=True)


def _escape_sql_value(val):
    """将 Python 值转义为 SQL 字面值"""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, datetime.datetime):
        return f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'"
    if isinstance(val, datetime.date):
        return f"'{val.strftime('%Y-%m-%d')}'"
    s = str(val).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return f"'{s}'"


async def _dump_database() -> tuple[str, str]:
    """导出全部表格：DDL（建表语句）和 DML（数据）分别返回"""
    ddl_buf = io.StringIO()
    dml_buf = io.StringIO()

    header = (
        f"-- MySQL Database Backup\n"
        f"-- Database: {settings.mysql_db}\n"
        f"-- Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"SET NAMES utf8mb4;\n\n"
    )
    ddl_buf.write(header)
    ddl_buf.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
    dml_buf.write(header)
    dml_buf.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

    async with engine.begin() as conn:
        result = await conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        total_tables = len(tables)

        for idx, table_name in enumerate(tables, 1):
            # ---- DDL ----
            ddl_buf.write(f"-- ----------------------------\n")
            ddl_buf.write(f"-- Table structure for `{table_name}` ({idx}/{total_tables})\n")
            ddl_buf.write(f"-- ----------------------------\n")

            ddl_result = await conn.execute(text(f"SHOW CREATE TABLE `{table_name}`"))
            ddl_row = ddl_result.fetchone()
            if ddl_row:
                create_sql = ddl_row[1]
                ddl_buf.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
                ddl_buf.write(create_sql + ";\n\n")

            # ---- DML ----
            dml_buf.write(f"-- ----------------------------\n")
            dml_buf.write(f"-- Data for `{table_name}` ({idx}/{total_tables})\n")
            dml_buf.write(f"-- ----------------------------\n")

            count_result = await conn.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
            row_count = count_result.scalar()

            if row_count == 0:
                dml_buf.write(f"-- 0 rows\n\n")
                continue

            col_result = await conn.execute(text(f"SELECT * FROM `{table_name}` LIMIT 0"))
            columns = list(col_result.keys())
            col_list = ", ".join(f"`{c}`" for c in columns)
            insert_prefix = f"INSERT INTO `{table_name}` ({col_list}) VALUES "

            batch_size = 500
            for offset in range(0, row_count, batch_size):
                rows_result = await conn.execute(
                    text(f"SELECT * FROM `{table_name}` LIMIT :limit OFFSET :offset"),
                    {"limit": batch_size, "offset": offset}
                )
                rows = rows_result.fetchall()

                values_list = []
                for row in rows:
                    vals = ", ".join(_escape_sql_value(v) for v in row)
                    values_list.append(f"({vals})")

                dml_buf.write(insert_prefix + ",\n".join(values_list) + ";\n\n")

            dml_buf.write(f"-- {row_count} rows total\n\n")

    ddl_buf.write("SET FOREIGN_KEY_CHECKS = 1;\n")
    dml_buf.write("SET FOREIGN_KEY_CHECKS = 1;\n")
    return ddl_buf.getvalue(), dml_buf.getvalue()


@router.get("/backups")
async def list_backups(admin: AdminUser):
    """获取备份列表（按组：每组含 DDL + DML 两个文件）"""
    groups: dict[str, dict] = {}
    if not os.path.exists(BACKUP_STORAGE_DIR):
        return {"items": []}

    for filename in sorted(os.listdir(BACKUP_STORAGE_DIR), reverse=True):
        if not filename.endswith(".sql"):
            continue
        filepath = os.path.join(BACKUP_STORAGE_DIR, filename)
        stat = os.stat(filepath)

        # 从文件名提取组标识: mathcoe_db_20260525_143000_ddl.sql / _data.sql
        base = filename.replace(".sql", "")
        is_ddl = base.endswith("_ddl")
        is_data = base.endswith("_data")

        if is_ddl:
            group_key = base[:-4]  # 去掉 _ddl
        elif is_data:
            group_key = base[:-5]  # 去掉 _data
        else:
            continue

        if group_key not in groups:
            groups[group_key] = {"id": group_key, "created_at": "", "ddl_file": None, "data_file": None}

        # 解析时间
        name_parts = group_key.split("_")
        created_at = ""
        if len(name_parts) >= 3:
            try:
                date_str = name_parts[-2]
                time_str = name_parts[-1]
                created_at = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
            except (IndexError, ValueError):
                created_at = datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        groups[group_key]["created_at"] = created_at or groups[group_key]["created_at"]

        file_info = {"filename": filename, "size": str(stat.st_size)}
        if is_ddl:
            groups[group_key]["ddl_file"] = file_info
        elif is_data:
            groups[group_key]["data_file"] = file_info

    items = sorted(groups.values(), key=lambda g: g["created_at"], reverse=True)
    return {"items": items}


@router.post("/backups")
async def create_backup(admin: AdminUser):
    """创建数据库备份（DDL 和数据分别生成文件）"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"mathcoe_db_{timestamp}"
    ddl_path = os.path.join(BACKUP_STORAGE_DIR, f"{base_name}_ddl.sql")
    data_path = os.path.join(BACKUP_STORAGE_DIR, f"{base_name}_data.sql")

    try:
        ddl_content, data_content = await _dump_database()

        with open(ddl_path, "w", encoding="utf-8") as f:
            f.write(ddl_content)
        with open(data_path, "w", encoding="utf-8") as f:
            f.write(data_content)

        ddl_size = os.stat(ddl_path).st_size
        data_size = os.stat(data_path).st_size
        logger.info(f"数据库备份成功: {base_name}, ddl={ddl_size}, data={data_size}")
        return {"message": "备份创建成功", "data": {"base_name": base_name, "ddl_size": str(ddl_size), "data_size": str(data_size)}}
    except Exception as e:
        for p in (ddl_path, data_path):
            if os.path.exists(p):
                os.remove(p)
        logger.error(f"备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"备份失败: {str(e)[:200]}")


@router.get("/backups/{backup_id}/download")
async def download_backup(backup_id: str, admin: AdminUser):
    """下载备份文件"""
    filepath = os.path.join(BACKUP_STORAGE_DIR, backup_id)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="备份文件不存在")

    return FileResponse(
        filepath,
        media_type="application/sql",
        filename=backup_id,
    )


@router.delete("/backups/{backup_id}")
async def delete_backup(backup_id: str, admin: AdminUser):
    """删除备份组（同时删除 DDL 和数据文件）"""
    deleted = []
    for suffix in ("_ddl.sql", "_data.sql"):
        filepath = os.path.join(BACKUP_STORAGE_DIR, f"{backup_id}{suffix}")
        if os.path.exists(filepath):
            os.remove(filepath)
            deleted.append(filepath)

    if not deleted:
        raise HTTPException(status_code=404, detail="备份文件不存在")
    logger.info(f"删除备份组: {backup_id}, files={deleted}")
    return {"message": "删除成功"}


# ============ 图片管理 ============

STATIC_DIR = os.path.realpath("app/static")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"}


def _scan_images(subdir: str = "") -> list[dict]:
    """Scan static directory (non-recursive) and return image file list."""
    base = os.path.join(STATIC_DIR, subdir) if subdir else STATIC_DIR
    if not os.path.isdir(base):
        return []

    results: list[dict] = []
    for entry in os.scandir(base):
        if not entry.is_file():
            continue
        ext = os.path.splitext(entry.name)[1].lower()
        if ext not in IMAGE_EXTENSIONS:
            continue

        rel_path = os.path.relpath(entry.path, STATIC_DIR)
        stat = entry.stat()
        results.append({
            "path": rel_path,
            "filename": entry.name,
            "directory": subdir,
            "size": stat.st_size,
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "url": f"{settings.server_host.rstrip('/')}/api/v1/static/{rel_path}",
        })
    return results


@router.get("/images")
async def list_images(
    admin: AdminUser,
    directory: str = Query("", description="子目录，如 uploads/202605"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
):
    """列出图片，支持按目录筛选和分页"""
    all_images = _scan_images(directory)
    total = len(all_images)

    start = (page - 1) * size
    end = start + size
    items = all_images[start:end]

    # 收集所有子目录（排除隐藏目录和非图片目录）
    EXCLUDED_DIRS = {"templates", "logs"}
    dirs = set()
    base = os.path.join(STATIC_DIR, directory) if directory else STATIC_DIR
    if os.path.isdir(base):
        for entry in os.scandir(base):
            if entry.is_dir() and not entry.name.startswith(".") and entry.name not in EXCLUDED_DIRS:
                dirs.add(entry.name)

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "subdirs": sorted(dirs),
        "current_directory": directory,
    }


@router.delete("/images")
async def delete_image(
    admin: AdminUser,
    path: str = Query(..., description="图片相对路径，如 uploads/202605/xxx.png"),
):
    """删除指定图片"""
    filepath = os.path.realpath(os.path.join(STATIC_DIR, path))
    if not filepath.startswith(STATIC_DIR):
        raise HTTPException(status_code=400, detail="非法路径")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="图片不存在")

    ext = os.path.splitext(path)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    os.remove(filepath)
    logger.info(f"删除图片: path={path}")
    return {"message": "删除成功"}


@router.post("/images/batch-delete")
async def batch_delete_images(
    admin: AdminUser,
    paths: list[str] = Body(...),
):
    """批量删除图片"""
    if not paths:
        raise HTTPException(status_code=400, detail="请提供要删除的图片路径")

    deleted = 0
    errors: list[dict] = []
    for path in paths:
        filepath = os.path.realpath(os.path.join(STATIC_DIR, path))
        if not filepath.startswith(STATIC_DIR):
            errors.append({"path": path, "message": "非法路径"})
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext not in IMAGE_EXTENSIONS:
            errors.append({"path": path, "message": "不支持的文件类型"})
            continue
        if not os.path.exists(filepath):
            errors.append({"path": path, "message": "图片不存在"})
            continue
        os.remove(filepath)
        deleted += 1

    logger.info(f"批量删除图片: total={len(paths)}, deleted={deleted}, errors={len(errors)}")
    return {"message": f"成功删除 {deleted} 张图片", "deleted": deleted, "errors": errors}


@router.post("/images/batch-download")
async def batch_download_images(
    admin: AdminUser,
    paths: list[str] = Body(...),
):
    """批量下载图片为 ZIP 包"""
    if not paths:
        raise HTTPException(status_code=400, detail="请提供要下载的图片路径")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            filepath = os.path.realpath(os.path.join(STATIC_DIR, path))
            if not filepath.startswith(STATIC_DIR) or not os.path.exists(filepath):
                continue
            # Use just the filename inside ZIP (avoid subdirectory nesting)
            arcname = os.path.basename(filepath)
            zf.write(filepath, arcname)

    buf.seek(0)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="images_{timestamp}.zip"'},
    )


@router.post("/images/upload")
async def upload_admin_image(
    admin: AdminUser,
    file: UploadFile = File(...),
    directory: str = Query("", description="目标目录，如 banners"),
):
    """上传图片到指定目录"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只支持图片文件")

    target_dir = os.path.join(STATIC_DIR, directory) if directory else STATIC_DIR
    os.makedirs(target_dir, exist_ok=True)

    ext = file.filename.split(".")[-1] if file.filename else "jpg"
    filename = f"{datetime.datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(target_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    rel_path = os.path.relpath(filepath, STATIC_DIR)
    url = f"{settings.server_host.rstrip('/')}/api/v1/static/{rel_path}"
    return {"url": url, "filename": filename, "path": rel_path}


@router.post("/images/sharpen")
async def sharpen_images(
    admin: AdminUser,
    paths: list[str] = Body(...),
):
    """对图片应用 OpenCV 锐化处理（Unsharp Mask），保存为原文件名 _sharpened 版本"""
    if not paths:
        raise HTTPException(status_code=400, detail="请提供要锐化的图片路径")

    results: list[dict] = []
    for path in paths:
        try:
            filepath = os.path.realpath(os.path.join(STATIC_DIR, path))
            if not filepath.startswith(STATIC_DIR):
                results.append({"path": path, "success": False, "message": "非法路径"})
                continue

            if not os.path.exists(filepath):
                results.append({"path": path, "success": False, "message": "图片不存在"})
                continue

            # Read image with OpenCV
            img = cv2.imread(filepath)
            if img is None:
                results.append({"path": path, "success": False, "message": "无法读取图片"})
                continue

            # --- 图片增强 ---
            # 1. 轻微降噪（保护画质）
            img = cv2.GaussianBlur(img, (1, 1), 0)

            # 2. 提高对比度
            img = cv2.convertScaleAbs(img, alpha=1.2, beta=10)

            # 3. 锐化
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharpened = cv2.filter2D(img, -1, kernel)

            # Save as _sharpened
            stem, ext = os.path.splitext(filepath)
            stem = stem.rstrip("_sharpened")  # prevent stacking
            out_path = f"{stem}_sharpened{ext}"
            cv2.imwrite(out_path, sharpened)

            rel_out = os.path.relpath(out_path, STATIC_DIR)
            url = f"{settings.server_host.rstrip('/')}/api/v1/static/{rel_out}"
            results.append({"path": rel_out, "success": True, "message": "锐化成功", "url": url})
        except Exception as e:
            logger.exception("图片锐化失败: path=%s", path)
            results.append({"path": path, "success": False, "message": f"处理异常: {e}"})

    success_count = sum(1 for r in results if r["success"])
    return {"message": f"锐化完成: {success_count}/{len(results)}", "results": results}