"""
Question schemas
"""
from datetime import datetime
from pydantic import BaseModel


class QuestionContent(BaseModel):
    """题目内容"""
    text: str | None = None
    images: list[str] | None = None


class QuestionOption(BaseModel):
    """题目选项"""
    label: str  # A, B, C, D
    text: str | None = None
    image: str | None = None


class QuestionExplanation(BaseModel):
    """答案解析"""
    text: str | None = None
    images: list[str] | None = None


class QuestionBase(BaseModel):
    title: str
    content: dict | None = None  # {text: str, images: []}
    question_type: str = "single"  # single 单选, multiple 多选
    options: list[dict] | None = None  # [{label: A, text: str, image: str}]
    answer: str  # 单选: "A", 多选: "A,B"
    explanation: dict | None = None  # {text: str, images: []}
    difficulty: str | None = None
    level: int  # 级别 1-6，必选
    source_year: int | None = None
    tags: list[str] | None = None


class QuestionCreate(QuestionBase):
    topic_id: int  # 所属专题，必选


class QuestionUpdate(BaseModel):
    title: str | None = None
    content: dict | None = None
    question_type: str | None = None
    options: list[dict] | None = None
    answer: str | None = None
    explanation: dict | None = None
    difficulty: str | None = None
    level: int | None = None  # 级别 1-6
    source_year: int | None = None
    tags: list[str] | None = None
    topic_id: int | None = None


class QuestionResponse(BaseModel):
    id: int
    topic_id: int | None
    title: str
    content: dict | None
    question_type: str
    options: list[dict] | None
    answer: str
    explanation: dict | None
    difficulty: str | None
    level: int | None  # 级别 1-6
    source_year: int | None
    tags: list[str] | None
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class QuestionForPractice(BaseModel):
    """题目（不含答案）"""
    id: int
    topic_id: int | None
    title: str
    content: dict | None
    question_type: str = "single"  # 默认单选题
    options: list[dict] | None
    difficulty: str | None
    level: int | None = 1  # 默认级别

    class Config:
        from_attributes = True


class QuestionForDiscover(BaseModel):
    """探索页面题目（含答案和解析）"""
    id: int
    topic_id: int | None
    title: str
    content: dict | None
    question_type: str = "single"
    options: list[dict] | None
    answer: str
    explanation: dict | None
    difficulty: str | None
    level: int | None = 1

    class Config:
        from_attributes = True