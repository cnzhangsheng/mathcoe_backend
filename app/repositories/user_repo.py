"""
User repository - data access for User model
"""
from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model"""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_openid(self, openid: str) -> User | None:
        """Get user by WeChat openid"""
        result = await self.session.execute(select(User).where(User.openid == openid))
        return result.scalar_one_or_none()

    async def create_or_get_by_openid(
        self,
        openid: str,
        nickname: str | None = None,
        avatar_url: str | None = None
    ) -> User:
        """Create user if not exists, otherwise update and return existing user"""
        user = await self.get_by_openid(openid)
        if user is None:
            # 创建新用户
            user = await self.create({
                "openid": openid,
                "nickname": nickname,
                "avatar_url": avatar_url,
                "last_login_at": datetime.now(),
            })
        else:
            # 用户已存在，更新用户信息（如果提供了）
            if nickname is not None:
                user.nickname = nickname
            if avatar_url is not None:
                user.avatar_url = avatar_url
            user.last_active_date = date.today()
            user.last_login_at = datetime.now()  # 更新最后登录时间
            await self.session.commit()
            await self.session.refresh(user)
        return user