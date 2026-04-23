"""
Admin authentication API - 管理员登录
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBSession
from app.core.security import create_access_token, verify_password
from app.models.admin import Admin
from app.schemas.admin import AdminLoginRequest, AdminLoginResponse, AdminResponse

router = APIRouter()


async def get_admin_by_username(db: AsyncSession, username: str) -> Admin | None:
    """根据用户名获取管理员"""
    result = await db.execute(select(Admin).where(Admin.username == username))
    return result.scalar_one_or_none()


async def get_current_admin(db: DBSession, token_data: dict) -> Admin:
    """从 token 获取当前管理员"""
    admin_id = token_data.get("admin_id")
    if not admin_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    return admin


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest, db: DBSession):
    """管理员登录"""
    admin = await get_admin_by_username(db, request.username)

    if not admin:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not verify_password(request.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 创建 JWT token
    token = create_access_token({"admin_id": admin.id, "username": admin.username, "role": admin.role})

    return AdminLoginResponse(
        token=token,
        admin_id=admin.id,
        username=admin.username,
        role=admin.role
    )


@router.get("/me", response_model=AdminResponse)
async def get_admin_info(db: DBSession, token_data: dict = Depends(lambda: {})):
    """获取当前管理员信息"""
    # TODO: 实现从 header 解析 token
    admin = await get_current_admin(db, token_data)
    return AdminResponse(
        id=admin.id,
        username=admin.username,
        role=admin.role,
        created_at=str(admin.created_at) if admin.created_at else None
    )