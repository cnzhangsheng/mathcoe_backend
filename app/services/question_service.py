"""
Question service - question related business logic
"""
import random
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.question_repo import QuestionRepository
from app.repositories.topic_repo import TopicRepository
from app.schemas.question import QuestionResponse, QuestionForPractice, QuestionForDiscover


class QuestionService:
    """Question related business logic"""

    def __init__(self, session: AsyncSession):
        self.question_repo = QuestionRepository(session)
        self.topic_repo = TopicRepository(session)

    async def get_questions(
        self,
        topic_id: int | None = None,
        year: int | None = None,
        limit: int = 20,
    ) -> list[QuestionForPractice]:
        """Get questions with filters"""
        if topic_id:
            questions = await self.question_repo.get_by_topic(topic_id, limit)
        elif year:
            questions = await self.question_repo.get_by_year(year, limit)
        else:
            questions = await self.question_repo.get_all(limit)

        return [
            QuestionForPractice(
                id=q.id,
                topic_id=q.topic_id,
                title=q.title,
                content=q.content,
                options=q.content.get("options") if q.content else None,
            )
            for q in questions
        ]

    async def get_question(self, question_id: int) -> QuestionResponse | None:
        """Get question by ID"""
        question = await self.question_repo.get_by_id(question_id)
        if question is None:
            return None
        return QuestionResponse.model_validate(question)

    async def get_random_question(self, level: int | None = None) -> QuestionForDiscover | None:
        """Get a random question for discover page, optionally filtered by level"""
        if level:
            questions = await self.question_repo.get_by_level(level, limit=100)
        else:
            questions = await self.question_repo.get_all(limit=100)
        if not questions:
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