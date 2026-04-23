"""
Question service - question related business logic
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.question_repo import QuestionRepository
from app.repositories.topic_repo import TopicRepository
from app.schemas.question import QuestionResponse, QuestionForPractice


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