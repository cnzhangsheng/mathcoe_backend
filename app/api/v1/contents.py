"""
Content management API - 内容管理
"""
import logging

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBSession
from app.models.content import Content
from app.schemas.content import ContentCreate, ContentUpdate, ContentResponse, ContentDetail
from app.utils.content import enhance_content_html

logger = logging.getLogger(__name__)

router = APIRouter(tags=["content"])


# ============ Admin API ============

@router.get("/admin/contents", response_model=list[ContentResponse])
async def list_contents(
    db: DBSession,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
):
    """获取内容列表"""
    query = select(Content).order_by(Content.created_at.desc())
    if status:
        query = query.where(Content.status == status)

    offset = (page - 1) * size
    result = await db.execute(query.offset(offset).limit(size))
    return result.scalars().all()


@router.get("/admin/contents/count")
async def count_contents(db: DBSession, status: str | None = None):
    """获取内容总数"""
    query = select(func.count(Content.id))
    if status:
        query = query.where(Content.status == status)
    result = await db.execute(query)
    return {"total": result.scalar()}


@router.get("/admin/contents/{content_id}", response_model=ContentResponse)
async def get_content(content_id: int, db: DBSession):
    """获取内容详情"""
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content


@router.post("/admin/contents", response_model=ContentResponse)
async def create_content(data: ContentCreate, db: DBSession):
    """创建内容"""
    content = Content(
        title=data.title,
        content=data.content or "",
        slug=data.slug or "",
        status=data.status or "draft",
    )
    # 保存后拿到 ID，然后 slug 使用 ID 值
    db.add(content)
    await db.commit()
    await db.refresh(content)

    # slug 使用 ID 值
    content.slug = str(content.id)
    await db.commit()
    await db.refresh(content)

    logger.info(f"内容已创建: id={content.id}, title={content.title}, slug={content.slug}")
    return content


@router.put("/admin/contents/{content_id}", response_model=ContentResponse)
async def update_content(content_id: int, data: ContentUpdate, db: DBSession):
    """更新内容"""
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(content, key, value)

    await db.commit()
    await db.refresh(content)
    return content


@router.delete("/admin/contents/{content_id}")
async def delete_content(content_id: int, db: DBSession):
    """删除内容"""
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    await db.delete(content)
    await db.commit()
    return {"success": True}


# ============ Public API ============

@router.get("/contents/{slug}/detail", response_model=ContentDetail)
async def get_content_by_slug(slug: str, db: DBSession):
    """获取已发布的内容（小程序端）"""
    result = await db.execute(
        select(Content).where(Content.slug == slug, Content.status == "published")
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在或未发布")

    return ContentDetail(
        title=content.title,
        content=enhance_content_html(content.content),
        slug=content.slug,
        updated_at=content.updated_at,
    )
