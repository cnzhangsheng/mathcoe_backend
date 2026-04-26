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
        difficulty: str | None = None,
        year: int | None = None,
        limit: int = 20,
    ) -> list[QuestionForPractice]:
        """Get questions with filters"""
        if topic_id:
            questions = await self.question_repo.get_by_topic(topic_id, limit)
        elif difficulty:
            questions = await self.question_repo.get_by_difficulty(difficulty, limit)
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
                difficulty=q.difficulty,
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

    async def get_random_question(self) -> QuestionForDiscover | None:
        """Get a random question for discover page"""
        questions = await self.question_repo.get_all(limit=100)
        if not questions:
            return None

        question = random.choice(questions)

        return QuestionForDiscover(
            id=question.id,
            topic_id=question.topic_id,
            title=question.title,
            content=question.content,
            question_type=question.question_type or "single",
            options=question.options,
            answer=question.answer,
            explanation=question.explanation,
            difficulty=question.difficulty,
            level=question.level,
        )