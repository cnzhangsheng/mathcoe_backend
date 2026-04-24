"""
Practice service - practice related business logic
"""
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.question_repo import QuestionRepository
from app.repositories.practice_repo import (
    PracticeRecordRepository,
    UserProgressRepository,
    WrongQuestionRepository,
    FavoriteRepository,
)
from app.schemas.practice import (
    PracticeStartResponse,
    PracticeSubmitResponse,
    PracticeRecordResponse,
    FavoriteResponse,
    WrongQuestionResponse,
)


class PracticeService:
    """Practice related business logic"""

    def __init__(self, session: AsyncSession):
        self.question_repo = QuestionRepository(session)
        self.record_repo = PracticeRecordRepository(session)
        self.progress_repo = UserProgressRepository(session)
        self.wrong_repo = WrongQuestionRepository(session)
        self.favorite_repo = FavoriteRepository(session)

    async def start_practice(
        self,
        user_id: int,
        topic_id: int | None = None,
        mode: str = "normal",
        difficulty: str | None = None,
        year: int | None = None,
    ) -> PracticeStartResponse:
        """Start a practice session"""
        # 根据条件获取题目
        if topic_id:
            questions = await self.question_repo.get_by_topic(topic_id, limit=10)
        elif difficulty:
            questions = await self.question_repo.get_by_difficulty(difficulty, limit=10)
        elif year:
            questions = await self.question_repo.get_by_year(year, limit=10)
        else:
            questions = await self.question_repo.get_all(limit=10)

        question_list = [
            {
                "id": q.id,
                "title": q.title,
                "content": q.content,
                "options": q.options,
                "answer": q.answer,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "level": q.level,
                "question_type": q.question_type,
            }
            for q in questions
        ]

        session_id = str(uuid.uuid4())
        time_limit = 2700 if mode == "exam" else None  # 模考45分钟

        return PracticeStartResponse(
            session_id=session_id,
            questions=question_list,
            total=len(question_list),
            time_limit=time_limit,
        )

    async def submit_answer(
        self,
        user_id: int,
        question_id: int,
        user_answer: str,
        time_spent: int | None = None,
    ) -> PracticeSubmitResponse:
        """Submit answer and check correctness"""
        question = await self.question_repo.get_by_id(question_id)
        if question is None:
            return PracticeSubmitResponse(is_correct=False, correct_answer="", explanation=None)

        is_correct = user_answer == question.answer

        # 记录答题
        await self.record_repo.create({
            "user_id": user_id,
            "question_id": question_id,
            "user_answer": user_answer,
            "is_correct": is_correct,
            "time_spent": time_spent,
        })

        # 错题记录
        if not is_correct:
            await self.wrong_repo.add_wrong_question(user_id, question_id)

        return PracticeSubmitResponse(
            is_correct=is_correct,
            correct_answer=question.answer,
            explanation=question.explanation,
        )

    async def get_records(self, user_id: int, limit: int = 50) -> list[PracticeRecordResponse]:
        """Get user practice records"""
        records = await self.record_repo.get_by_user(user_id, limit)
        return [
            PracticeRecordResponse(
                id=r.id,
                question_id=r.question_id,
                question_title=None,
                user_answer=r.user_answer,
                is_correct=r.is_correct,
                time_spent=r.time_spent,
                created_at=r.created_at,
            )
            for r in records
        ]

    async def get_favorites(self, user_id: int) -> list[FavoriteResponse]:
        """Get user favorites"""
        favorites = await self.favorite_repo.get_by_user(user_id)
        return [
            FavoriteResponse(
                id=f.id,
                question_id=f.question_id,
                question_title=None,
                created_at=f.created_at,
            )
            for f in favorites
        ]

    async def add_favorite(self, user_id: int, question_id: int) -> FavoriteResponse:
        """Add question to favorites"""
        favorite = await self.favorite_repo.create({
            "user_id": user_id,
            "question_id": question_id,
        })
        return FavoriteResponse(
            id=favorite.id,
            question_id=favorite.question_id,
            created_at=favorite.created_at,
        )

    async def remove_favorite(self, user_id: int, question_id: int) -> bool:
        """Remove question from favorites"""
        return await self.favorite_repo.remove_favorite(user_id, question_id)

    async def get_wrong_questions(self, user_id: int) -> list[WrongQuestionResponse]:
        """Get user wrong questions"""
        wrong_list = await self.wrong_repo.get_by_user(user_id)
        return [
            WrongQuestionResponse(
                id=w.id,
                question_id=w.question_id,
                question_title=None,
                retry_count=w.retry_count,
                mastered=w.mastered,
                created_at=w.created_at,
            )
            for w in wrong_list
        ]