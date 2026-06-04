"""
Question repository - data access for Question model
"""
from sqlalchemy import select, func, or_, Integer, Float, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
        published_only: bool = True, offset: int = 0,
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

        result = await self.session.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def get_by_year(self, year: int, limit: int = 20, published_only: bool = True, offset: int = 0) -> list[Question]:
        """Get questions by source year"""
        query = select(Question).where(Question.source_year == year)
        if published_only:
            query = query.where(Question.status == "published")
        result = await self.session.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def get_by_level(self, level: int, limit: int = 100, published_only: bool = True, offset: int = 0) -> list[Question]:
        """Get questions by difficulty level (1-6)"""
        query = select(Question).where(Question.difficulty_level == level)
        if published_only:
            query = query.where(Question.status == "published")
        result = await self.session.execute(query.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def get_all(self, limit: int = 100, offset: int = 0, published_only: bool = True, sort_by: str = "default", level: int | None = None) -> list[Question]:
        """Get all questions with pagination, optionally filtered by published status and level"""
        query = select(Question)
        if published_only:
            query = query.where(Question.status == "published")
        if level is not None:
            query = query.where(Question.difficulty_level == level)

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

    async def search_by_content(self, keyword: str, level: int | None = None, topic_id: int | None = None, page: int = 1, size: int = 20) -> tuple[list[Question], int]:
        """按题目内容模糊搜索，支持按难度和专题过滤"""
        query = (
            select(Question)
            .options(selectinload(Question.topic))
            .where(
                Question.content["text"].as_string().ilike(f"%{keyword}%"),
                Question.status == "published",
            )
        )
        if level is not None:
            query = query.where(Question.difficulty_level == level)
        if topic_id is not None:
            query = query.where(Question.topic_id == topic_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * size
        query = query.order_by(Question.id.desc()).offset(offset).limit(size)
        result = await self.session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def get_rankings(self, level: int) -> dict:
        """获取指定Level的收藏TOP20和易错TOP20"""
        from app.models.practice_record import PracticeRecord

        # 收藏TOP20：按收藏的不同用户数降序
        fav_subquery = (
            select(
                Favorite.question_id,
                func.count(func.distinct(Favorite.user_id)).label("fav_count"),
            )
            .group_by(Favorite.question_id)
            .subquery()
        )

        hot_query = (
            select(Question, fav_subquery.c.fav_count)
            .options(selectinload(Question.topic))
            .join(fav_subquery, Question.id == fav_subquery.c.question_id)
            .where(Question.difficulty_level == level, Question.status == "published")
            .order_by(fav_subquery.c.fav_count.desc())
            .limit(20)
        )
        hot_result = await self.session.execute(hot_query)
        hot_rows = hot_result.all()

        # 易错TOP20：按错误率降序（答错用户数/答题用户数，要求答题人数≥5）
        wrong_subquery = (
            select(
                PracticeRecord.question_id,
                func.count(func.distinct(PracticeRecord.user_id)).label("total_users"),
                func.sum(case((PracticeRecord.is_correct == False, 1), else_=0)).label("wrong_users"),
            )
            .group_by(PracticeRecord.question_id)
            .having(func.count(func.distinct(PracticeRecord.user_id)) >= 5)
            .subquery()
        )

        wrong_query = (
            select(Question, wrong_subquery.c.total_users, wrong_subquery.c.wrong_users)
            .options(selectinload(Question.topic))
            .join(wrong_subquery, Question.id == wrong_subquery.c.question_id)
            .where(Question.difficulty_level == level, Question.status == "published")
            .order_by(
                (
                    wrong_subquery.c.wrong_users.cast(Float)
                    / wrong_subquery.c.total_users.cast(Float)
                ).desc()
            )
            .limit(20)
        )
        wrong_result = await self.session.execute(wrong_query)
        wrong_rows = wrong_result.all()

        return {
            "hot_rows": hot_rows,
            "wrong_rows": wrong_rows,
        }