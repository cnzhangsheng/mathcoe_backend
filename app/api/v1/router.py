"""
V1 API router aggregation
"""
from fastapi import APIRouter

from app.api.v1 import auth, user, topic, question, practice, favorites, admin_auth, admin, upload, exam_paper, discover

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(user.router, prefix="/users", tags=["users"])
router.include_router(topic.router, prefix="/topics", tags=["topics"])
router.include_router(question.router, prefix="/questions", tags=["questions"])
router.include_router(exam_paper.router, prefix="/exam-papers", tags=["exam-papers"])
router.include_router(practice.router, prefix="/practice", tags=["practice"])
router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
router.include_router(discover.router, prefix="/discover", tags=["discover"])
router.include_router(admin_auth.router, prefix="/admin", tags=["admin-auth"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(upload.router, tags=["upload"])