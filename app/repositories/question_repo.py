"""
Question repository - data access for Question model
"""
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.like import Like
from app.models.favorite import Favorite, WrongQuestion
from app.repositories.base import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    """Repository for Question model"""

    def __init__(self, session: AsyncSession):
        super().__init__(Question, session)

    async def get_by_topic(
        self, topic_id: int, limit: int = 20, level: int | None = None, sort_by: str = "default",
        published_only: bool = True,
    ) -> list[Question]:
        """Get questions by topic ID, optionally filtered by level and sorted

        sort_by options:
            - default: no explicit ordering
            - time: order by created_at DESC
            - random: random order (MySQL RAND())
            - likes: order by total like count DESC
            - favorites: order by total favorite count DESC
            - wrong_count: order by total wrong count (sum of retry_count) DESC
        """
        query = select(Question).where(Question.topic_id == topic_id)
        if level is not None:
            query = query.where(Question.difficulty_level == level)
        if published_only:
            query = query.where(Question.status == "published")

        if sort_by == "time":
            query = query.order_by(Question.created_at.desc())
        elif sort_by == "random":
            query = query.order_by(func.rand())
        elif sort_by == "likes":
            like_subq = (
                select(Like.question_id, func.count(Like.id).label("like_count"))
                .group_by(Like.question_id)
                .subquery()
            )
            query = query.outerjoin(like_subq, like_subq.c.question_id == Question.id)
            query = query.order_by(func.coalesce(like_subq.c.like_count, 0).desc())
        elif sort_by == "favorites":
            favorite_subq = (
                select(Favorite.question_id, func.count(Favorite.id).label("favorite_count"))
                .group_by(Favorite.question_id)
                .subquery()
            )
            query = query.outerjoin(favorite_subq, favorite_subq.c.question_id == Question.id)
            query = query.order_by(func.coalesce(favorite_subq.c.favorite_count, 0).desc())
        elif sort_by == "wrong_count":
            wrong_subq = (
                select(WrongQuestion.question_id, func.sum(WrongQuestion.retry_count).label("wrong_count"))
                .group_by(WrongQuestion.question_id)
                .subquery()
            )
            query = query.outerjoin(wrong_subq, wrong_subq.c.question_id == Question.id)
            query = query.order_by(func.coalesce(wrong_subq.c.wrong_count, 0).desc())

        result = await self.session.execute(query.limit(limit))
        return list(result.scalars().all())

    async def get_by_year(self, year: int, limit: int = 20, published_only: bool = True) -> list[Question]:
        """Get questions by source year"""
        query = select(Question).where(Question.source_year == year)
        if published_only:
            query = query.where(Question.status == "published")
        result = await self.session.execute(query.limit(limit))
        return list(result.scalars().all())

    async def get_by_level(self, level: int, limit: int = 100, published_only: bool = True) -> list[Question]:
        """Get questions by difficulty level (1-6)"""
        query = select(Question).where(Question.difficulty_level == level)
        if published_only:
            query = query.where(Question.status == "published")
        result = await self.session.execute(query.limit(limit))
        return list(result.scalars().all())

    async def get_all(self, limit: int = 100, offset: int = 0, published_only: bool = True, sort_by: str = "default") -> list[Question]:
        """Get all questions with pagination, optionally filtered by published status"""
        query = select(Question)
        if published_only:
            query = query.where(Question.status == "published")

        if sort_by == "favorites":
            favorite_subq = (
                select(Favorite.question_id, func.count(Favorite.id).label("favorite_count"))
                .group_by(Favorite.question_id)
                .subquery()
            )
            query = query.outerjoin(favorite_subq, favorite_subq.c.question_id == Question.id)
            query = query.order_by(func.coalesce(favorite_subq.c.favorite_count, 0).desc())

        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())