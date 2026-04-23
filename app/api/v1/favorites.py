"""
Favorites API router - favorites and wrong questions
"""
from fastapi import APIRouter

from app.api.deps import DBSession, CurrentUser
from app.schemas.practice import FavoriteRequest, FavoriteResponse, WrongQuestionResponse
from app.services.practice_service import PracticeService

router = APIRouter()


@router.get("", response_model=list[FavoriteResponse])
async def get_favorites(db: DBSession, current_user: CurrentUser):
    """Get user favorites"""
    service = PracticeService(db)
    return await service.get_favorites(current_user["id"])


@router.post("", response_model=FavoriteResponse)
async def add_favorite(request: FavoriteRequest, db: DBSession, current_user: CurrentUser):
    """Add question to favorites"""
    service = PracticeService(db)
    return await service.add_favorite(current_user["id"], request.question_id)


@router.delete("")
async def remove_favorite(request: FavoriteRequest, db: DBSession, current_user: CurrentUser):
    """Remove question from favorites"""
    service = PracticeService(db)
    success = await service.remove_favorite(current_user["id"], request.question_id)
    return {"success": success}


@router.get("/wrong", response_model=list[WrongQuestionResponse])
async def get_wrong_questions(db: DBSession, current_user: CurrentUser):
    """Get user wrong questions"""
    service = PracticeService(db)
    return await service.get_wrong_questions(current_user["id"])