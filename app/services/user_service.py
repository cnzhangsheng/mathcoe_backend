"""
User service - user related business logic
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repo import UserRepository
from app.repositories.practice_repo import UserProgressRepository, PracticeRecordRepository
from app.schemas.user import UserResponse, UserProgressResponse, UserAbilityRadar


class UserService:
    """User related business logic"""

    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.progress_repo = UserProgressRepository(session)
        self.record_repo = PracticeRecordRepository(session)

    async def get_user(self, user_id: int) -> UserResponse | None:
        """Get user by ID"""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return None
        return UserResponse.model_validate(user)

    async def get_user_progress(self, user_id: int) -> list[UserProgressResponse]:
        """Get user progress for all topics"""
        progress_list = await self.progress_repo.get_all_by_user(user_id)
        return [
            UserProgressResponse(
                topic_id=p.topic_id,
                topic_title=None,  # 需要额外查询 topic
                progress=p.progress,
                success_rate=p.success_rate,
                questions_done=p.questions_done,
            )
            for p in progress_list
        ]

    async def get_user_ability_radar(self, user_id: int) -> UserAbilityRadar:
        """Calculate user ability radar based on practice records"""
        # 基于练习记录计算各能力维度分数
        abilities = [
            {"label": "逻辑推理", "value": 85, "color": "bg-blue-400"},
            {"label": "空间想象", "value": 60, "color": "bg-purple-400"},
            {"label": "算术应用", "value": 75, "color": "bg-green-400"},
            {"label": "规律总结", "value": 90, "color": "bg-amber-400"},
        ]
        # TODO: 基于实际数据计算
        return UserAbilityRadar(abilities=abilities, overall_rank=82)