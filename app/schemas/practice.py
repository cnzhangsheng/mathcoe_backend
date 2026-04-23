"""
Practice schemas
"""
from datetime import datetime
from pydantic import BaseModel


class PracticeStartRequest(BaseModel):
    topic_id: int | None = None  # 专题练习
    mode: str = "normal"  # normal / exam
    difficulty: str | None = None
    year: int | None = None  # 历年真题


class PracticeStartResponse(BaseModel):
    session_id: str  # 本次练习会话ID
    questions: list[dict]
    total: int
    time_limit: int | None = None  # 模考限时（秒）


class PracticeSubmitRequest(BaseModel):
    question_id: int
    user_answer: str  # A/B/C/D
    time_spent: int | None = None  # 用时（秒）


class PracticeSubmitResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str | None


class PracticeRecordResponse(BaseModel):
    id: int
    question_id: int
    question_title: str | None = None
    user_answer: str | None
    is_correct: bool | None
    time_spent: int | None
    created_at: datetime | None

    class Config:
        from_attributes = True


class FavoriteRequest(BaseModel):
    question_id: int


class FavoriteResponse(BaseModel):
    id: int
    question_id: int
    question_title: str | None = None
    created_at: datetime | None

    class Config:
        from_attributes = True


class WrongQuestionResponse(BaseModel):
    id: int
    question_id: int
    question_title: str | None = None
    retry_count: int
    mastered: bool
    created_at: datetime | None

    class Config:
        from_attributes = True