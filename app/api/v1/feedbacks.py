"""
Feedback API - 用户意见反馈
"""
import logging

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import DBSession, CurrentUser, AdminUser
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackUpdate, FeedbackResponse, FeedbackAdminResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])


# ============ User API ============


@router.post("/feedbacks", response_model=FeedbackResponse)
async def create_feedback(data: FeedbackCreate, db: DBSession, current_user: CurrentUser):
    """用户提交反馈"""
    feedback = Feedback(
        user_id=current_user["id"],
        content=data.content,
        contact=data.contact,
        status="pending",
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    logger.info(f"反馈已提交: user_id={current_user['id']}, feedback_id={feedback.id}")
    return feedback


# ============ Admin API ============


@router.get("/admin/feedbacks", response_model=list[FeedbackAdminResponse])
async def list_feedbacks(
    db: DBSession,
    admin: AdminUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
):
    """管理员查看反馈列表"""
    query = select(Feedback).order_by(Feedback.created_at.desc())
    if status:
        query = query.where(Feedback.status == status)
    offset = (page - 1) * size
    result = await db.execute(query.offset(offset).limit(size))
    return result.scalars().all()


@router.get("/admin/feedbacks/{feedback_id}", response_model=FeedbackAdminResponse)
async def get_feedback(feedback_id: int, db: DBSession, admin: AdminUser):
    """管理员查看反馈详情"""
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    return feedback


@router.put("/admin/feedbacks/{feedback_id}", response_model=FeedbackAdminResponse)
async def update_feedback(feedback_id: int, data: FeedbackUpdate, db: DBSession, admin: AdminUser):
    """管理员回复/更新反馈状态"""
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(feedback, key, value)

    await db.commit()
    await db.refresh(feedback)
    return feedback