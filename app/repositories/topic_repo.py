"""
Topic repository - data access for Topic model
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic
from app.repositories.base import BaseRepository


class TopicRepository(BaseRepository[Topic]):
    """Repository for Topic model"""

    def __init__(self, session: AsyncSession):
        super().__init__(Topic, session)

    async def get_high_freq_topics(self) -> list[Topic]:
        """Get high frequency topics"""
        result = await self.session.execute(select(Topic).where(Topic.is_high_freq == True))
        return list(result.scalars().all())