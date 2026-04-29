"""
Question repository - data access for Question model
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.repositories.base import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    """Repository for Question model"""

    def __init__(self, session: AsyncSession):
        super().__init__(Question, session)

    async def get_by_topic(self, topic_id: int, limit: int = 20, level: int | None = None) -> list[Question]:
        """Get questions by topic ID, optionally filtered by level"""
        query = select(Question).where(Question.topic_id == topic_id)
        if level is not None:
            query = query.where(Question.difficulty_level == level)
        result = await self.session.execute(query.limit(limit))
        return list(result.scalars().all())

    async def get_by_year(self, year: int, limit: int = 20) -> list[Question]:
        """Get questions by source year"""
        result = await self.session.execute(
            select(Question).where(Question.source_year == year).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_level(self, level: int, limit: int = 100) -> list[Question]:
        """Get questions by difficulty level (1-6)"""
        result = await self.session.execute(
            select(Question).where(Question.difficulty_level == level).limit(limit)
        )
        return list(result.scalars().all())