"""
Question schemas
"""
import re
from datetime import datetime
from pydantic import BaseModel, model_serializer

from app.core.config import settings
from app.utils.helpers import process_img_url


class BaseQuestionSchema(BaseModel):
    """Base class for schemas containing question HTML content.

    Automatically prefixes relative /api/v1/static/ image URLs with the
    configured server_host during serialization.
    """

    @model_serializer(mode="wrap")
    def _process_html_urls(self, nxt):
        data = nxt(self)
        base_url = settings.server_host.rstrip("/")

        content_fields = {"content", "explanation", "question_content", "question_explanation"}
        for field in content_fields:
            if field in data and isinstance(data[field], dict) and "text" in data[field]:
                data[field] = dict(data[field], text=process_img_url(data[field].get("text", ""), base_url))

        options_fields = {"options", "question_options"}
        for field in options_fields:
            if field in data and isinstance(data[field], list):
                data[field] = [
                    dict(opt, text=process_img_url(opt.get("text", ""), base_url))
                    if isinstance(opt, dict) else opt
                    for opt in data[field]
                ]

        if "questions" in data and isinstance(data["questions"], list):
            data["questions"] = [
                _process_question_dict(q, base_url) if isinstance(q, dict) else q
                for q in data["questions"]
            ]

        return data


def _process_question_dict(d: dict, base_url: str) -> dict:
    """Process HTML fields in a single question dict (for PracticeStartResponse.questions etc.)"""
    result = dict(d)
    for field in ("content", "explanation"):
        if field in result and isinstance(result[field], dict) and "text" in result[field]:
            result[field] = dict(result[field], text=process_img_url(result[field].get("text", ""), base_url))
    if "options" in result and isinstance(result["options"], list):
        result["options"] = [
            dict(opt, text=process_img_url(opt.get("text", ""), base_url))
            if isinstance(opt, dict) else opt
            for opt in result["options"]
        ]
    return result


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
    difficulty_level: int  # 级别 1-6，必选
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
    difficulty_level: int | None = None  # 级别 1-6
    source_year: int | None = None
    tags: list[str] | None = None
    topic_id: int | None = None


class QuestionResponse(BaseQuestionSchema):
    id: int
    topic_id: int | None
    title: str
    content: dict | None
    question_type: str
    options: list[dict] | None
    answer: str
    explanation: dict | None
    difficulty_level: int | None  # 级别 1-6
    source_year: int | None
    tags: list[str] | None
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class QuestionForPractice(BaseQuestionSchema):
    """题目（不含答案）"""
    id: int
    topic_id: int | None
    title: str
    content: dict | None
    question_type: str = "single"  # 默认单选题
    options: list[dict] | None
    difficulty_level: int | None = 1  # 默认级别

    class Config:
        from_attributes = True


class QuestionForDiscover(BaseQuestionSchema):
    """探索页面题目（含答案和解析）"""
    id: int
    topic_id: int | None
    topic_title: str | None = None
    title: str
    content: dict | None
    question_type: str = "single"
    options: list[dict] | None
    answer: str
    explanation: dict | None
    difficulty_level: int | None = 1

    class Config:
        from_attributes = True