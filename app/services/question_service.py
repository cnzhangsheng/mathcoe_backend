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

    async def search_questions(
        self,
        keyword: str,
        level: int | None = None,
        topic_id: int | None = None,
        page: int = 1,
        size: int = 20,
        tag: str | None = None,
    ) -> tuple[list[dict], int]:
        """按内容搜索已发布的题目"""
        questions, total = await self.question_repo.search_by_content(
            keyword, level, topic_id, page, size, tag
        )
        items = []
        for q in questions:
            content_text = ""
            if q.content and isinstance(q.content, dict):
                content_text = q.content.get("text", "")
            items.append({
                "id": q.id,
                "content": content_text,
                "difficulty_level": q.difficulty_level,
                "topic_title": q.topic.title if q.topic else "未分类",
                "question_type": q.question_type,
            })
        return items, total

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

    async def get_random_question(
        self, level: int | None = None, user_id: int | None = None,
        exclude_ids: set[int] | None = None,
    ) -> QuestionForDiscover | None:
        """Get a random question for discover page, with weighted selection.

        Weighting: questions with higher ID (newer) have higher probability.
        Filters:
          - exclude_ids: already shown in current session
          - practice_records: questions the user has already done (correct or wrong)
        Falls back to unfiltered pool when all questions have been seen.
        """
        # 1. 拉取大池子（最多 2000 条）
        if level:
            questions = await self.question_repo.get_by_level(level, limit=2000)
        else:
            questions = await self.question_repo.get_all(limit=2000)
        if not questions:
            return None

        # 2. 过滤掉本次会话已看过的
        if exclude_ids:
            questions = [q for q in questions if q.id not in exclude_ids]

        # 3. 过滤掉用户做过的所有题（含正确和错误）
        if user_id:
            done_ids_result = await self.session.execute(
                select(PracticeRecord.question_id)
                .where(PracticeRecord.user_id == user_id)
                .distinct()
            )
            done_ids = {row[0] for row in done_ids_result.all()}
            if done_ids:
                questions = [q for q in questions if q.id not in done_ids]

        # 4. 如果过滤完空了，降级：只排除 session 已看过，不排除做过的
        if not questions and exclude_ids:
            logger.info("当前池子已无全新题，降级为仅排除已看过的")
            if level:
                questions = await self.question_repo.get_by_level(level, limit=2000)
            else:
                questions = await self.question_repo.get_all(limit=2000)
            if exclude_ids:
                questions = [q for q in questions if q.id not in exclude_ids]

        # 5. 如果还是空（极端情况所有题都看过了），去掉所有排除条件
        if not questions:
            logger.info("所有题目均已被看过，从头开始循环")
            if level:
                questions = await self.question_repo.get_by_level(level, limit=2000)
            else:
                questions = await self.question_repo.get_all(limit=2000)
            if not questions:
                return None

        # 6. 按 ID 加权随机（ID 越大 = 越新 = 权重越高）
        min_id = min(q.id for q in questions)
        weights = [q.id - min_id + 1 for q in questions]
        question = random.choices(questions, weights=weights, k=1)[0]

        logger.info(
            f"加权随机选题: user_id={user_id}, level={level}, "
            f"pool={len(questions)}, chosen_id={question.id}"
        )

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