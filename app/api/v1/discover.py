"""
Discover API router - random question for explore page
"""
import logging
from fastapi import APIRouter

from app.api.deps import DBSession, UserOrNone
from app.repositories.user_repo import UserRepository
from app.schemas.question import QuestionForDiscover
from app.services.question_service import QuestionService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/random", response_model=QuestionForDiscover)
async def get_random_question(db: DBSession, user: UserOrNone = None):
    """Get a random question for discover page.
    Authenticated users get questions matched to their difficulty level.
    Unauthenticated users get a random question without level filtering.
    """
    difficulty_level = None
    if user:
        logger.info(f"获取随机题目: user_id={user['id']}")
        user_repo = UserRepository(db)
        db_user = await user_repo.get_by_id(user['id'])
        difficulty_level = db_user.difficulty_level if db_user else None
        logger.info(f"用户难度等级: {difficulty_level}")
    else:
        logger.info("获取随机题目: 未登录用户")

    service = QuestionService(db)
    question = await service.get_random_question(level=difficulty_level)
    if question is None:
        logger.warning(f"没有可用的题目")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="暂无题目")
    logger.info(f"随机题目返回: question_id={question.id}, level={difficulty_level}")
    return question