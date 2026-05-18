"""
Banner management API - Banner 配置管理
"""
import logging

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBSession
from app.models.banner import Banner
from app.schemas.banner import BannerCreate, BannerUpdate, BannerResponse, BannerPublic

logger = logging.getLogger(__name__)

router = APIRouter(tags=["banner"])


# ============ Admin API ============

@router.get("/admin/banners", response_model=list[BannerResponse])
async def list_banners(
    db: DBSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    """获取 Banner 列表"""
    query = select(Banner).order_by(Banner.sort_order.asc(), Banner.created_at.desc())

    offset = (page - 1) * size
    result = await db.execute(query.offset(offset).limit(size))
    return result.scalars().all()


@router.get("/admin/banners/{banner_id}", response_model=BannerResponse)
async def get_banner(banner_id: int, db: DBSession):
    """获取 Banner 详情"""
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner不存在")
    return banner


@router.post("/admin/banners", response_model=BannerResponse)
async def create_banner(data: BannerCreate, db: DBSession):
    """创建 Banner"""
    banner = Banner(
        image_url=data.image_url,
        link_type=data.link_type,
        link_value=data.link_value,
        title=data.title,
        position=data.position,
        sort_order=data.sort_order,
        is_active=data.is_active,
    )
    db.add(banner)
    await db.commit()
    await db.refresh(banner)
    logger.info(f"Banner已创建: id={banner.id}, title={banner.title}")
    return banner


@router.put("/admin/banners/{banner_id}", response_model=BannerResponse)
async def update_banner(banner_id: int, data: BannerUpdate, db: DBSession):
    """更新 Banner"""
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(banner, key, value)

    await db.commit()
    await db.refresh(banner)
    return banner


@router.delete("/admin/banners/{banner_id}")
async def delete_banner(banner_id: int, db: DBSession):
    """删除 Banner"""
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner不存在")

    await db.delete(banner)
    await db.commit()
    return {"success": True}


# ============ Public API (小程序端) ============

@router.get("/banners", response_model=list[BannerPublic])
async def list_active_banners(
    db: DBSession,
    position: str | None = Query(None),
):
    """获取已启用的 Banner 列表（按 sort_order 排序）"""
    query = select(Banner).where(
        Banner.is_active == True
    )
    if position:
        query = query.where(Banner.position == position)
    query = query.order_by(Banner.sort_order.asc(), Banner.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()
