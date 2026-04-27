"""
User service - user related business logic
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.topic import Topic
from app.repositories.user_repo import UserRepository
from app.repositories.practice_repo import UserProgressRepository, PracticeRecordRepository, WrongQuestionRepository, FavoriteRepository
from app.schemas.user import UserResponse, UserProgressResponse, UserAbilityRadar, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    """User related business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.progress_repo = UserProgressRepository(session)
        self.record_repo = PracticeRecordRepository(session)
        self.wrong_repo = WrongQuestionRepository(session)
        self.favorite_repo = FavoriteRepository(session)

    def get_week_range(self) -> tuple[datetime, datetime]:
        """Get current week start and end (Monday to Sunday)"""
        now = datetime.now()
        # 找到本周周一
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        week_start = now - timedelta(days=weekday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        # 本周结束（下周一）
        week_end = week_start + timedelta(days=7)
        return week_start, week_end

    async def get_user(self, user_id: int) -> UserResponse | None:
        """Get user by ID"""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return None
        return UserResponse.model_validate(user)

    async def get_user_progress(self, user_id: int) -> list[UserProgressResponse]:
        """Get user progress for all topics with topic title"""
        progress_list = await self.progress_repo.get_all_by_user_with_topic(user_id)
        return [
            UserProgressResponse(
                topic_id=p["topic_id"],
                topic_title=p["topic_title"],
                progress=p["progress"],
                success_rate=p["success_rate"],
                questions_done=p["questions_done"],
            )
            for p in progress_list
        ]

    async def get_user_ability_radar(self, user_id: int) -> UserAbilityRadar:
        """Calculate user ability radar based on 5 topics"""
        # 获取所有专题
        topics_result = await self.session.execute(
            select(Topic).order_by(Topic.id)
        )
        topics = list(topics_result.scalars().all())

        # 获取用户在所有专题上的进度
        progress_list = await self.progress_repo.get_all_by_user_with_topic(user_id)

        # 构建进度字典，方便查找
        progress_map = {p["topic_id"]: p for p in progress_list}

        # 构建能力雷达：每个专题一个能力维度
        abilities = []
        total_success_rate = 0
        total_questions = 0
        topic_count = 0

        for topic in topics:
            progress_data = progress_map.get(topic.id)

            if progress_data:
                # 有进度数据，使用实际数据
                success_rate = progress_data["success_rate"]
                questions_done = progress_data["questions_done"]
                total_success_rate += success_rate * questions_done
                total_questions += questions_done
            else:
                # 没有进度数据，显示为0
                success_rate = 0
                questions_done = 0

            abilities.append({
                "label": topic.title,  # 直接使用专题名称
                "value": success_rate,
            })
            topic_count += 1

        # 计算整体排名
        # 基于加权平均正确率和练习量
        avg_success_rate = round(total_success_rate / total_questions) if total_questions > 0 else 0

        # 排名算法：正确率 * 0.7 + 练习量因子 * 0.3
        # 练习量因子：每10题贡献5分，上限50分
        practice_factor = min(50, (total_questions // 10) * 5)
        overall_rank = min(99, round(avg_success_rate * 0.7 + practice_factor * 0.3))

        return UserAbilityRadar(
            abilities=abilities,
            overall_rank=overall_rank
        )

    async def get_user_stats(self, user_id: int) -> dict:
        """Get user learning statistics for current week"""
        week_start, week_end = self.get_week_range()

        # 本周答题统计
        week_stats = await self.record_repo.get_user_stats_by_week(user_id, week_start, week_end)

        # 本周新增错题数量
        wrong_questions = await self.wrong_repo.get_by_user(user_id, mastered=False)
        wrong_count = len(wrong_questions)

        # 收藏数量（总收藏）
        favorites = await self.favorite_repo.get_by_user(user_id)
        favorite_count = len(favorites)

        return {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "total_questions": week_stats["total"],
            "correct_count": week_stats["correct"],
            "wrong_count": week_stats["wrong"],
            "correct_rate": week_stats["success_rate"],
            "total_wrong_count": wrong_count,  # 总错题数
            "favorite_count": favorite_count,
        }

    async def update_user(self, user_id: int, data: UserUpdate) -> UserResponse | None:
        """Update user information"""
        update_data = data.model_dump(exclude_unset=True)
        user = await self.user_repo.update(user_id, update_data)
        if user is None:
            return None
        return UserResponse.model_validate(user)