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
        avatar_url: str | None = None,
        grade: str = "G1",
        difficulty_level: int = 1
    ) -> User:
        """Create user if not exists, otherwise update and return existing user"""
        user = await self.get_by_openid(openid)
        default_nickname = "数学小达人"
        if user is None:
            # 创建新用户，昵称默认为"数学小达人"
            user = await self.create({
                "openid": openid,
                "nickname": nickname or default_nickname,
                "avatar_url": avatar_url,
                "grade": grade,
                "difficulty_level": difficulty_level,
                "last_login_at": datetime.now(),
            })
        else:
            # 用户已存在，更新用户信息（如果提供了）
            if nickname is not None:
                user.nickname = nickname
            if avatar_url is not None:
                user.avatar_url = avatar_url
            user.grade = grade
            user.difficulty_level = difficulty_level
            user.last_active_date = date.today()
            user.last_login_at = datetime.now()
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def update(self, user_id: int, data: dict) -> User | None:
        """Update user fields by user_id

        Args:
            user_id: The user's ID
            data: Dictionary of fields to update (only non-None values with existing attributes are updated)

        Returns:
            Updated User object or None if user not found
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        for key, value in data.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)

        await self.session.commit()
        await self.session.refresh(user)
        return user