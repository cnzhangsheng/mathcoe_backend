"""
Question service - question related business logic
"""
import logging
import random

from sqlalchemy import select, func, cast, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.practice_record import PracticeRecord
from app.repositories.question_repo import QuestionRepository
from app.repositories.topic_repo import TopicRepository
from app.schemas.question import QuestionResponse, QuestionForPractice, QuestionForDiscover

logger = logging.getLogger(__name__)


class QuestionService:
    """Question related business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.question_repo = QuestionRepository(session)
        self.topic_repo = TopicRepository(session)

    async def get_recommended_questions(
        self,
        user_id: int,
        level: int | None = None,
        limit: int = 10,
    ) -> list[QuestionForPractice]:
        """Get recommended questions based on user's weakest topic and level"""
        logger.info(f"开始推荐题目分析: user_id={user_id}, level={level}, limit={limit}")
        # 1. 分析用户薄弱专题（正确率最低）
        topic_stats = await self.session.execute(
            select(
                Question.topic_id,
                func.count(PracticeRecord.id).label("total"),
                func.sum(cast(PracticeRecord.is_correct, Integer)).label("correct"),
            )
            .select_from(PracticeRecord)
            .join(Question, PracticeRecord.question_id == Question.id)
            .where(PracticeRecord.user_id == user_id)
            .group_by(Question.topic_id)
            .order_by(func.sum(cast(PracticeRecord.is_correct, Integer)) / func.count(PracticeRecord.id))
            .limit(1)
        )
        row = topic_stats.first()

        if row and row.topic_id:
            # 有练习记录 → 取最薄弱专题的题目，按用户等级过滤
            accuracy = (row.correct / row.total * 100) if row.total > 0 else 0
            logger.info(f"找到薄弱专题: topic_id={row.topic_id}, 正确率={accuracy:.1f}% ({row.correct}/{row.total})")
            questions = await self.question_repo.get_by_topic(
                row.topic_id, limit=limit, level=level, sort_by="default"
            )
        else:
            # 无练习记录 → 按收藏数倒序推荐，按用户等级过滤
            logger.info(f"用户无练习记录，按收藏数倒序推荐: user_id={user_id}, level={level}")
            questions = await self.question_repo.get_all(limit=limit, sort_by="favorites", level=level)

        logger.info(f"推荐题目查询完成: user_id={user_id}, 返回{len(questions)}道题目")

        return [
            QuestionForPractice(
                id=q.id,
                topic_id=q.topic_id,
                title=q.title,
                content=q.content,
                options=q.content.get("options") if q.content else None,
                difficulty_level=q.difficulty_level,
            )
            for q in questions
        ]

    async def get_questions(
        self,
        topic_id: int | None = None,
        year: int | None = None,
        limit: int = 20,
        sort_by: str = "default",
        level: int | None = None,
    ) -> list[QuestionForPractice]:
        """Get questions with filters"""
        if topic_id:
            questions = await self.question_repo.get_by_topic(topic_id, limit, level=level, sort_by=sort_by)
        elif year:
            questions = await self.question_repo.get_by_year(year, limit)
        else:
            questions = await self.question_repo.get_all(limit, sort_by=sort_by)

        return [
            QuestionForPractice(
                id=q.id,
                topic_id=q.topic_id,
                title=q.title,
                content=q.content,
                options=q.content.get("options") if q.content else None,
                difficulty_level=q.difficulty_level,
            )
            for q in questions
        ]

    async def get_question(self, question_id: int) -> QuestionResponse | None:
        """Get question by ID"""
        question = await self.question_repo.get_by_id(question_id)
        if question is None:
            return None
        return QuestionResponse.model_validate(question)

    async def get_random_question(self, level: int | None = None, user_id: int | None = None) -> QuestionForDiscover | None:
        """Get a random question for discover page, optionally filtered by level.
        If user_id is provided, filters out questions the user has already answered correctly.
        """
        if level:
            questions = await self.question_repo.get_by_level(level, limit=100)
        else:
            questions = await self.question_repo.get_all(limit=100)
        if not questions:
            return None

        # 过滤掉用户已答对的题目
        if user_id:
            correct_ids_result = await self.session.execute(
                select(PracticeRecord.question_id)
                .where(
                    PracticeRecord.user_id == user_id,
                    PracticeRecord.is_correct == True,
                )
                .distinct()
            )
            correct_ids = {row[0] for row in correct_ids_result.all()}
            if correct_ids:
                questions = [q for q in questions if q.id not in correct_ids]
                if not questions:
                    logger.info(f"用户 {user_id} 所有题目均已答对，无新题可选")
                    return None

        question = random.choice(questions)

        return QuestionForDiscover(
            id=question.id,
            topic_id=question.topic_id,
            topic_title=question.topic.title if question.topic else None,
            title=question.title,
            content=question.content,
            question_type=question.question_type or "single",
            options=question.options,
            answer=question.answer,
            explanation=question.explanation,
            difficulty_level=question.difficulty_level,
        )