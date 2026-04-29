"""
Schemas module - Pydantic models for request/response validation
"""
from app.schemas.auth import WeChatLoginRequest, WeChatLoginResponse, TokenResponse
from app.schemas.user import UserResponse, UserAbilityRadar, UserInsightResponse
from app.schemas.topic import TopicResponse, TopicWithProgress
from app.schemas.question import QuestionResponse, QuestionForPractice
from app.schemas.practice import (
    PracticeStartRequest,
    PracticeStartResponse,
    PracticeSubmitRequest,
    PracticeSubmitResponse,
    PracticeRecordResponse,
    FavoriteRequest,
    FavoriteResponse,
    WrongQuestionResponse,
)

__all__ = [
    "WeChatLoginRequest",
    "WeChatLoginResponse",
    "TokenResponse",
    "UserResponse",
    "UserAbilityRadar",
    "UserInsightResponse",
    "TopicResponse",
    "TopicWithProgress",
    "QuestionResponse",
    "QuestionForPractice",
    "PracticeStartRequest",
    "PracticeStartResponse",
    "PracticeSubmitRequest",
    "PracticeSubmitResponse",
    "PracticeRecordResponse",
    "FavoriteRequest",
    "FavoriteResponse",
    "WrongQuestionResponse",
]