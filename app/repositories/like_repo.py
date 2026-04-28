"""
Like repository - data access for Like model
"""
import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.like import Like
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class LikeRepository(BaseRepository[Like]):
    """Repository for Like model"""

    def __init__(self, session: AsyncSession):
        super().__init__(Like, session)

    async def is_liked(self, user_id: int, question_id: int) -> bool:
        """Check if question is liked by user"""
        result = await self.session.execute(
            select(Like.id)
            .where(Like.user_id == user_id)
            .where(Like.question_id == question_id)
        )
        return result.scalar_one_or_none() is not None

    async def add_like(self, user_id: int, question_id: int) -> Like:
        """Add like"""
        like = await self.create({
            "user_id": user_id,
            "question_id": question_id,
        })
        return like

    async def remove_like(self, user_id: int, question_id: int) -> bool:
        """Remove like"""
        result = await self.session.execute(
            select(Like)
            .where(Like.user_id == user_id)
            .where(Like.question_id == question_id)
        )
        like = result.scalar_one_or_none()
        if like is None:
            return False
        await self.session.delete(like)
        await self.session.commit()
        return True

    async def get_like_count(self, question_id: int) -> int:
        """Get like count for a question"""
        result = await self.session.execute(
            select(func.count(Like.id))
            .where(Like.question_id == question_id)
        )
        return result.scalar() or 0