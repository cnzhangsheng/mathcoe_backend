"""
Practice repository - data access for PracticeRecord, UserProgress, Favorite, WrongQuestion
"""
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.practice_record import PracticeRecord
from app.models.user_progress import UserProgress
from app.models.favorite import Favorite, WrongQuestion
from app.repositories.base import BaseRepository


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

    async def get_user_stats(self, user_id: int) -> dict:
        """Get user practice statistics"""
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
            select(UserProgress).where(UserProgress.user_id == user_id)
        )
        return list(result.scalars().all())


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

    async def add_wrong_question(self, user_id: int, question_id: int) -> WrongQuestion:
        """Add or update wrong question"""
        result = await self.session.execute(
            select(WrongQuestion)
            .where(WrongQuestion.user_id == user_id)
            .where(WrongQuestion.question_id == question_id)
        )
        wrong = result.scalar_one_or_none()
        if wrong is None:
            wrong = await self.create({
                "user_id": user_id,
                "question_id": question_id,
            })
        else:
            wrong.retry_count += 1
            wrong.last_retry_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(wrong)
        return wrong