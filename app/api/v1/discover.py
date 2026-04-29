"""
Discover API router - random question for explore page
"""
import logging
from fastapi import APIRouter

from app.api.deps import DBSession, CurrentUser
from app.repositories.user_repo import UserRepository
from app.schemas.question import QuestionForDiscover
from app.services.question_service import QuestionService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/random", response_model=QuestionForDiscover)
async def get_random_question(db: DBSession, user: CurrentUser):
    """Get a random question for discover page, matched to user's difficulty level"""
    logger.info(f"获取随机题目: user_id={user['id']}")

    # 获取用户的难度等级
    user_repo = UserRepository(db)
    db_user = await user_repo.get_by_id(user['id'])
    difficulty_level = db_user.difficulty_level if db_user else None
    logger.info(f"用户难度等级: {difficulty_level}")

    service = QuestionService(db)
    question = await service.get_random_question(level=difficulty_level)
    if question is None:
        logger.warning(f"没有可用的题目")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="暂无题目")
    logger.info(f"随机题目返回: question_id={question.id}, level={difficulty_level}")
    return question