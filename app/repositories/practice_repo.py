"""
Practice repository - data access for PracticeRecord, UserProgress, Favorite, WrongQuestion
"""
import logging
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.practice_record import PracticeRecord
from app.models.user_progress import UserProgress
from app.models.favorite import Favorite, WrongQuestion
from app.models.question import Question
from app.repositories.base import BaseRepository
from app.utils import short_id

logger = logging.getLogger(__name__)


class PracticeRecordRepository(BaseRepository[PracticeRecord]):
    """Repository for PracticeRecord model"""

    def __init__(self, session: AsyncSession):
        super().__init__(PracticeRecord, session)

    async def get_by_user(self, user_id: int, limit: int = 50) -> list[PracticeRecord]:
        """Get practice records by user ID"""
        result = await self.session.execute(
            select(PracticeRecord)
            .where(PracticeRecord.user_id == user_id)
            .order_by(PracticeRecord.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user_with_question(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        topic_id: int | None = None,
        time_filter: str | None = None,
        result_filter: str | None = None,
    ) -> list[PracticeRecord]:
        """Get practice records by user ID with question and topic info, with filters"""
        from sqlalchemy import and_

        # 构建查询条件
        conditions = [PracticeRecord.user_id == user_id]

        # 专题筛选
        if topic_id:
            conditions.append(Question.topic_id == topic_id)

        # 时间筛选
        if time_filter:
            now = datetime.utcnow()
            if time_filter == "day":
                # 今天
                day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                conditions.append(PracticeRecord.created_at >= day_start)
            elif time_filter == "week":
                # 本周（从周一开始）
                from datetime import timedelta
                week_start = now - timedelta(days=now.weekday())
                week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                conditions.append(PracticeRecord.created_at >= week_start)
            elif time_filter == "month":
                # 本月
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                conditions.append(PracticeRecord.created_at >= month_start)

        # 结果筛选
        if result_filter:
            if result_filter == "correct":
                conditions.append(PracticeRecord.is_correct == True)
            elif result_filter == "wrong":
                conditions.append(PracticeRecord.is_correct == False)

        query = (
            select(PracticeRecord)
            .options(
                selectinload(PracticeRecord.question),
                selectinload(PracticeRecord.question).selectinload(Question.topic)
            )
            .join(Question, PracticeRecord.question_id == Question.id, isouter=True)
            .where(and_(*conditions))
            .order_by(PracticeRecord.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: int,
        topic_id: int | None = None,
        time_filter: str | None = None,
        result_filter: str | None = None,
    ) -> int:
        """Get total count of practice records for a user with filters"""
        from sqlalchemy import and_, func

        conditions = [PracticeRecord.user_id == user_id]

        # 专题筛选
        if topic_id:
            conditions.append(Question.topic_id == topic_id)

        # 时间筛选
        if time_filter:
            now = datetime.utcnow()
            if time_filter == "day":
                day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                conditions.append(PracticeRecord.created_at >= day_start)
            elif time_filter == "week":
                from datetime import timedelta
                week_start = now - timedelta(days=now.weekday())
                week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                conditions.append(PracticeRecord.created_at >= week_start)
            elif time_filter == "month":
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                conditions.append(PracticeRecord.created_at >= month_start)

        # 结果筛选
        if result_filter:
            if result_filter == "correct":
                conditions.append(PracticeRecord.is_correct == True)
            elif result_filter == "wrong":
                conditions.append(PracticeRecord.is_correct == False)

        query = (
            select(func.count(PracticeRecord.id))
            .join(Question, PracticeRecord.question_id == Question.id, isouter=True)
            .where(and_(*conditions))
        )

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_user_stats(self, user_id: int) -> dict:
        """Get user practice statistics (all time)"""
        total_result = await self.session.execute(
            select(func.count(PracticeRecord.id)).where(PracticeRecord.user_id == user_id)
        )
        correct_result = await self.session.execute(
            select(func.count(PracticeRecord.id))
            .where(PracticeRecord.user_id == user_id)
            .where(PracticeRecord.is_correct == True)
        )
        total = total_result.scalar() or 0
        correct = correct_result.scalar() or 0
        return {
            "total": total,
            "correct": correct,
            "success_rate": round(correct / total * 100) if total > 0 else 0,
        }

    async def get_today_stats(self, user_id: int) -> dict:
        """Get user practice statistics for today"""
        now = datetime.utcnow()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 今日答题总数
        total_result = await self.session.execute(
            select(func.count(PracticeRecord.id))
            .where(PracticeRecord.user_id == user_id)
            .where(PracticeRecord.created_at >= day_start)
        )

        # 今日正确数量
        correct_result = await self.session.execute(
            select(func.count(PracticeRecord.id))
            .where(PracticeRecord.user_id == user_id)
            .where(PracticeRecord.created_at >= day_start)
            .where(PracticeRecord.is_correct == True)
        )

        total = total_result.scalar() or 0
        correct = correct_result.scalar() or 0

        return {
            "total": total,
            "correct": correct,
            "success_rate": round(correct / total * 100) if total > 0 else 0,
        }

    async def get_user_stats_by_week(self, user_id: int, week_start: datetime, week_end: datetime) -> dict:
        """Get user practice statistics for a specific week"""
        from sqlalchemy import and_

        # 本周答题总数
        total_result = await self.session.execute(
            select(func.count(PracticeRecord.id))
            .where(and_(
                PracticeRecord.user_id == user_id,
                PracticeRecord.created_at >= week_start,
                PracticeRecord.created_at < week_end
            ))
        )

        # 本周正确数量
        correct_result = await self.session.execute(
            select(func.count(PracticeRecord.id))
            .where(and_(
                PracticeRecord.user_id == user_id,
                PracticeRecord.created_at >= week_start,
                PracticeRecord.created_at < week_end,
                PracticeRecord.is_correct == True
            ))
        )

        # 本周错题数量
        wrong_result = await self.session.execute(
            select(func.count(PracticeRecord.id))
            .where(and_(
                PracticeRecord.user_id == user_id,
                PracticeRecord.created_at >= week_start,
                PracticeRecord.created_at < week_end,
                PracticeRecord.is_correct == False
            ))
        )

        total = total_result.scalar() or 0
        correct = correct_result.scalar() or 0
        wrong = wrong_result.scalar() or 0

        return {
            "total": total,
            "correct": correct,
            "wrong": wrong,
            "success_rate": round(correct / total * 100) if total > 0 else 0,
        }


class UserProgressRepository(BaseRepository[UserProgress]):
    """Repository for UserProgress model"""

    def __init__(self, session: AsyncSession):
        super().__init__(UserProgress, session)

    async def get_by_user_topic(self, user_id: int, topic_id: int) -> UserProgress | None:
        """Get user progress for a specific topic"""
        result = await self.session.execute(
            select(UserProgress)
            .where(UserProgress.user_id == user_id)
            .where(UserProgress.topic_id == topic_id)
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int) -> list[UserProgress]:
        """Get all progress for a user"""
        result = await self.session.execute(
            select(UserProgress)
            .options(selectinload(UserProgress.topic))
            .where(UserProgress.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_all_by_user_with_topic(self, user_id: int) -> list[dict]:
        """Get all progress for a user with topic info"""
        result = await self.session.execute(
            select(UserProgress)
            .options(selectinload(UserProgress.topic))
            .where(UserProgress.user_id == user_id)
        )
        progress_list = result.scalars().all()
        return [
            {
                "topic_id": p.topic_id,
                "topic_title": p.topic.title if p.topic else None,
                "progress": p.progress,
                "success_rate": p.success_rate,
                "questions_done": p.questions_done,
            }
            for p in progress_list
        ]


class FavoriteRepository(BaseRepository[Favorite]):
    """Repository for Favorite model"""

    def __init__(self, session: AsyncSession):
        super().__init__(Favorite, session)

    async def get_by_user(self, user_id: int) -> list[Favorite]:
        """Get user favorites"""
        result = await self.session.execute(
            select(Favorite).where(Favorite.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_by_user_with_question(self, user_id: int) -> list[Favorite]:
        """Get user favorites with question loaded"""
        result = await self.session.execute(
            select(Favorite)
            .options(
                selectinload(Favorite.question),
                selectinload(Favorite.question).selectinload(Question.topic)
            )
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
        )
        return list(result.scalars().all())

    async def is_favorited(self, user_id: int, question_id: int) -> bool:
        """Check if question is favorited by user"""
        result = await self.session.execute(
            select(Favorite.id)
            .where(Favorite.user_id == user_id)
            .where(Favorite.question_id == question_id)
        )
        return result.scalar_one_or_none() is not None

    async def remove_favorite(self, user_id: int, question_id: int) -> bool:
        """Remove favorite"""
        result = await self.session.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id)
            .where(Favorite.question_id == question_id)
        )
        favorite = result.scalar_one_or_none()
        if favorite is None:
            return False
        await self.session.delete(favorite)
        await self.session.commit()
        return True


class WrongQuestionRepository(BaseRepository[WrongQuestion]):
    """Repository for WrongQuestion model"""

    def __init__(self, session: AsyncSession):
        super().__init__(WrongQuestion, session)

    async def get_by_user(self, user_id: int, mastered: bool = False) -> list[WrongQuestion]:
        """Get user wrong questions"""
        result = await self.session.execute(
            select(WrongQuestion)
            .where(WrongQuestion.user_id == user_id)
            .where(WrongQuestion.mastered == mastered)
        )
        return list(result.scalars().all())

    async def get_by_user_with_question(self, user_id: int, mastered: bool = False) -> list[WrongQuestion]:
        """Get user wrong questions with question loaded"""
        result = await self.session.execute(
            select(WrongQuestion)
            .options(
                selectinload(WrongQuestion.question),
                selectinload(WrongQuestion.question).selectinload(Question.topic)
            )
            .where(WrongQuestion.user_id == user_id)
            .where(WrongQuestion.mastered == mastered)
            .order_by(WrongQuestion.created_at.desc())
        )
        return list(result.scalars().all())

    async def add_wrong_question(self, user_id: int, question_id: int) -> WrongQuestion:
        """Add or update wrong question"""
        logger.info(f"添加错题: user_id={user_id}, question_id={question_id}")
        result = await self.session.execute(
            select(WrongQuestion)
            .where(WrongQuestion.user_id == user_id)
            .where(WrongQuestion.question_id == question_id)
        )
        wrong = result.scalar_one_or_none()
        if wrong is None:
            logger.info(f"创建新错题记录: user_id={user_id}, question_id={question_id}")
            wrong = await self.create({
                "id": short_id(),
                "user_id": user_id,
                "question_id": question_id,
            })
        else:
            wrong.retry_count += 1
            wrong.last_retry_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(wrong)
            logger.info(f"更新错题记录: user_id={user_id}, question_id={question_id}, retry_count={wrong.retry_count}")
        return wrong

    async def mark_mastered(self, user_id: int, question_id: int) -> bool:
        """Mark wrong question as mastered"""
        logger.info(f"标记掌握: user_id={user_id}, question_id={question_id}")
        result = await self.session.execute(
            select(WrongQuestion)
            .where(WrongQuestion.user_id == user_id)
            .where(WrongQuestion.question_id == question_id)
        )
        wrong = result.scalar_one_or_none()
        if wrong is None:
            logger.warning(f"错题不存在: user_id={user_id}, question_id={question_id}")
            return False
        wrong.mastered = True
        await self.session.commit()
        logger.info(f"标记掌握成功: user_id={user_id}, question_id={question_id}")
        return True

    async def remove_wrong(self, user_id: int, question_id: int) -> bool:
        """Remove wrong question record"""
        logger.info(f"删除错题记录: user_id={user_id}, question_id={question_id}")
        result = await self.session.execute(
            select(WrongQuestion)
            .where(WrongQuestion.user_id == user_id)
            .where(WrongQuestion.question_id == question_id)
        )
        wrong = result.scalar_one_or_none()
        if wrong is None:
            logger.warning(f"错题不存在: user_id={user_id}, question_id={question_id}")
            return False
        await self.session.delete(wrong)
        await self.session.commit()
        logger.info(f"删除错题成功: user_id={user_id}, question_id={question_id}")
        return True