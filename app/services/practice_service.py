"""
Practice service - practice related business logic
"""
import logging
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.repositories.question_repo import QuestionRepository
from app.repositories.practice_repo import (
    PracticeRecordRepository,
    UserProgressRepository,
    WrongQuestionRepository,
    FavoriteRepository,
)
from app.models.exam_paper_test_answer import TestAnswerRecord
from app.schemas.practice import (
    PracticeStartResponse,
    PracticeSubmitResponse,
    PracticeRecordResponse,
    FavoriteResponse,
    WrongQuestionResponse,
    WrongQuestionDetailResponse,
    FavoriteDetailResponse,
)

logger = logging.getLogger(__name__)


class PracticeService:
    """Practice related business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
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
        logger.info(f"开始练习: user_id={user_id}, topic_id={topic_id}, mode={mode}")
        # 根据条件获取题目
        if topic_id:
            questions = await self.question_repo.get_by_topic(topic_id, limit=10)
        elif difficulty:
            questions = await self.question_repo.get_by_difficulty(difficulty, limit=10)
        elif year:
            questions = await self.question_repo.get_by_year(year, limit=10)
        else:
            questions = await self.question_repo.get_all(limit=10)

        logger.info(f"获取题目完成: count={len(questions)}")

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
        logger.info(f"提交答案: user_id={user_id}, question_id={question_id}, user_answer={user_answer}")
        question = await self.question_repo.get_by_id(question_id)
        if question is None:
            logger.warning(f"题目不存在: question_id={question_id}")
            return PracticeSubmitResponse(is_correct=False, correct_answer="", explanation=None)

        is_correct = user_answer == question.answer
        logger.info(f"答案检查: is_correct={is_correct}, correct_answer={question.answer}")

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
            logger.info(f"添加错题记录: user_id={user_id}, question_id={question_id}")
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

    async def get_favorites(self, user_id: int) -> list[FavoriteDetailResponse]:
        """Get user favorites with full question info"""
        favorites = await self.favorite_repo.get_by_user_with_question(user_id)
        return [
            FavoriteDetailResponse(
                id=f.id,
                question_id=f.question_id,
                question_title=f.question.title if f.question else None,
                question_content=f.question.content if f.question else None,
                question_options=f.question.options if f.question else None,
                question_answer=f.question.answer if f.question else None,
                question_explanation=f.question.explanation if f.question else None,
                question_difficulty=f.question.difficulty if f.question else None,
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

    async def get_wrong_questions(self, user_id: int) -> list[WrongQuestionDetailResponse]:
        """Get user wrong questions with full question info and last wrong answer"""
        logger.info(f"获取错题列表: user_id={user_id}")
        wrong_list = await self.wrong_repo.get_by_user_with_question(user_id)
        logger.info(f"错题列表获取完成: count={len(wrong_list)}")

        result = []
        for w in wrong_list:
            # 获取最近一次错误答案
            last_wrong_answer = await self._get_last_wrong_answer(self.session, user_id, w.question_id)

            result.append(WrongQuestionDetailResponse(
                id=w.id,
                question_id=w.question_id,
                question_title=w.question.title if w.question else None,
                question_topic_id=w.question.topic_id if w.question else None,
                question_topic_title=w.question.topic.title if w.question and w.question.topic else None,
                question_content=w.question.content if w.question else None,
                question_options=w.question.options if w.question else None,
                question_answer=w.question.answer if w.question else None,
                question_explanation=w.question.explanation if w.question else None,
                question_difficulty=w.question.difficulty if w.question else None,
                user_answer=last_wrong_answer,
                retry_count=w.retry_count,
                mastered=w.mastered,
                created_at=w.created_at,
            ))
        return result

    async def add_wrong_question(self, user_id: int, question_id: int) -> WrongQuestionResponse:
        """Add question to wrong questions list"""
        logger.info(f"添加错题: user_id={user_id}, question_id={question_id}")
        wrong_question = await self.wrong_repo.add_wrong_question(user_id, question_id)
        logger.info(f"错题添加成功: wrong_question_id={wrong_question.id}")
        return WrongQuestionResponse(
            id=wrong_question.id,
            question_id=wrong_question.question_id,
            retry_count=wrong_question.retry_count,
            mastered=wrong_question.mastered,
            created_at=wrong_question.created_at,
        )

    async def _get_last_wrong_answer(self, session: AsyncSession, user_id: int, question_id: int) -> str | None:
        """Get user's last wrong answer for a question"""
        result = await session.execute(
            select(TestAnswerRecord)
            .where(TestAnswerRecord.user_id == user_id)
            .where(TestAnswerRecord.question_id == question_id)
            .where(TestAnswerRecord.is_correct == False)
            .order_by(TestAnswerRecord.created_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
        return record.user_answer if record else None

    async def mark_wrong_mastered(self, user_id: int, question_id: int) -> bool:
        """Mark a wrong question as mastered"""
        logger.info(f"标记错题已掌握: user_id={user_id}, question_id={question_id}")
        result = await self.wrong_repo.mark_mastered(user_id, question_id)
        logger.info(f"标记掌握结果: success={result}")
        return result

    async def remove_wrong_question(self, user_id: int, question_id: int) -> bool:
        """Remove a wrong question from the list"""
        logger.info(f"删除错题: user_id={user_id}, question_id={question_id}")
        result = await self.wrong_repo.remove_wrong(user_id, question_id)
        logger.info(f"删除错题结果: success={result}")
        return result