"""
Practice schemas
"""
from datetime import datetime
from pydantic import BaseModel

from app.schemas.question import BaseQuestionSchema


class PracticeStartRequest(BaseModel):
    topic_id: int | None = None  # 专题练习
    mode: str = "normal"  # normal / exam
    year: int | None = None  # 历年真题
    sort_by: str = "default"  # 题目排序: default / time / random / likes / favorites / wrong_count


class PracticeStartResponse(BaseQuestionSchema):
    session_id: str  # 本次练习会话ID
    questions: list[dict]
    total: int
    time_limit: int | None = None  # 模考限时（秒）


class PracticeSubmitRequest(BaseModel):
    question_id: int
    user_answer: str  # A/B/C/D
    time_spent: int | None = None  # 用时（秒）


class PracticeSubmitResponse(BaseQuestionSchema):
    is_correct: bool
    correct_answer: str
    explanation: str | dict | None = None


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


class WrongQuestionRequest(BaseModel):
    question_id: int
    user_answer: str | None = None


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
    user_answer: str | None = None
    retry_count: int
    mastered: bool
    last_retry_at: datetime | None = None
    created_at: datetime | None

    class Config:
        from_attributes = True


class WrongQuestionDetailResponse(BaseQuestionSchema):
    """错题详情响应 - 包含完整题目信息"""
    id: int
    question_id: int
    question_title: str | None = None
    question_topic_id: int | None = None
    question_topic_title: str | None = None
    question_content: dict | None = None
    question_options: list[dict] | None = None
    question_answer: str | None = None
    question_explanation: dict | None = None
    question_difficulty_level: int | None = None
    user_answer: str | None = None  # 最近一次错误答案
    retry_count: int
    mastered: bool
    last_retry_at: datetime | None = None
    created_at: datetime | None

    class Config:
        from_attributes = True


class FavoriteDetailResponse(BaseQuestionSchema):
    """收藏详情响应 - 包含完整题目信息"""
    id: int
    question_id: int
    question_title: str | None = None
    question_topic_id: int | None = None
    question_topic_title: str | None = None
    question_content: dict | None = None
    question_options: list[dict] | None = None
    question_answer: str | None = None
    question_explanation: dict | None = None
    question_difficulty_level: int | None = None
    question_type: str = "single"
    created_at: datetime | None

    class Config:
        from_attributes = True


class PracticeRecordDetailResponse(BaseQuestionSchema):
    """答题记录详情响应 - 包含完整题目信息"""
    id: int
    question_id: int
    question_title: str | None = None
    question_topic_id: int | None = None
    question_topic_title: str | None = None
    question_content: dict | None = None
    question_options: list[dict] | None = None
    question_answer: str | None = None
    question_type: str = "single"
    user_answer: str | None
    is_correct: bool | None
    time_spent: int | None
    created_at: datetime | None

    class Config:
        from_attributes = True


class PracticeRecordsPaginatedResponse(BaseModel):
    """答题记录分页响应"""
    records: list[PracticeRecordDetailResponse]
    total: int
    page: int
    page_size: int
    stats: dict


class WrongQuestionsPaginatedResponse(BaseModel):
    """错题列表分页响应"""
    items: list[WrongQuestionDetailResponse]
    total: int
    page: int
    page_size: int


class FavoritesPaginatedResponse(BaseModel):
    """收藏列表分页响应"""
    items: list[FavoriteDetailResponse]
    total: int
    page: int
    page_size: int