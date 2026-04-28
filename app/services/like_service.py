"""
Like service - like related business logic
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.like_repo import LikeRepository
from app.schemas.like import LikeResponse

logger = logging.getLogger(__name__)


class LikeService:
    """Like related business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.like_repo = LikeRepository(session)

    async def is_liked(self, user_id: int, question_id: int) -> bool:
        """Check if user has liked a question"""
        return await self.like_repo.is_liked(user_id, question_id)

    async def add_like(self, user_id: int, question_id: int) -> LikeResponse:
        """Add like to question"""
        logger.info(f"添加点赞: user_id={user_id}, question_id={question_id}")
        like = await self.like_repo.add_like(user_id, question_id)
        logger.info(f"点赞添加成功: like_id={like.id}")
        return LikeResponse(
            id=like.id,
            question_id=like.question_id,
            created_at=like.created_at,
        )

    async def remove_like(self, user_id: int, question_id: int) -> bool:
        """Remove like from question"""
        logger.info(f"取消点赞: user_id={user_id}, question_id={question_id}")
        result = await self.like_repo.remove_like(user_id, question_id)
        logger.info(f"取消点赞结果: success={result}")
        return result

    async def get_like_count(self, question_id: int) -> int:
        """Get like count for a question"""
        return await self.like_repo.get_like_count(question_id)