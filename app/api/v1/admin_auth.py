"""
Admin authentication API - 管理员登录
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DBSession, AdminUser
from app.core.security import create_access_token, verify_password
from app.models.admin import Admin
from app.schemas.admin import AdminLoginRequest, AdminLoginResponse, AdminResponse

router = APIRouter()


async def get_admin_by_username(db: AsyncSession, username: str) -> Admin | None:
    """根据用户名获取管理员"""
    result = await db.execute(select(Admin).where(Admin.username == username))
    return result.scalar_one_or_none()


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
async def get_admin_info(admin: AdminUser, db: DBSession):
    """获取当前管理员信息"""
    from app.models.admin import Admin as AdminModel
    result = await db.execute(select(AdminModel).where(AdminModel.id == admin["admin_id"]))
    admin_obj = result.scalar_one_or_none()
    if not admin_obj:
        raise HTTPException(status_code=404, detail="管理员不存在")
    return AdminResponse(
        id=admin_obj.id,
        username=admin_obj.username,
        role=admin_obj.role,
        created_at=str(admin_obj.created_at) if admin_obj.created_at else None
    )