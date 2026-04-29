"""
Topic API router - topic training
"""
from fastapi import APIRouter

from app.api.deps import DBSession, CurrentUser
from app.schemas.topic import TopicResponse, TopicWithProgress
from app.repositories.topic_repo import TopicRepository
from app.models.topic import Topic

router = APIRouter()


@router.get("", response_model=list[TopicResponse])
async def get_topics(db: DBSession, limit: int = 10):
    """Get all topics"""
    repo = TopicRepository(db)
    topics = await repo.get_all(limit)
    return [TopicResponse.model_validate(t) for t in topics]


@router.get("/{topic_id}", response_model=TopicWithProgress)
async def get_topic(topic_id: int, db: DBSession, current_user: CurrentUser):
    """Get topic with user progress"""
    topic_repo = TopicRepository(db)

    topic = await topic_repo.get_by_id(topic_id)
    if topic is None:
        return None

    return TopicWithProgress(
        id=topic.id,
        title=topic.title,
        description=topic.description,
        difficulty=topic.difficulty,
        icon=topic.icon,
        color=topic.color,
        is_high_freq=topic.is_high_freq,
        progress=0,
        success_rate=0,
        questions_done=0,
    )