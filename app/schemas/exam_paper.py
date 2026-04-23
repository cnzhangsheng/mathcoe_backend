"""
ExamPaper schemas - 考卷相关数据结构
"""
from datetime import datetime
from pydantic import BaseModel


# ============ Question Basic Schema ============

class QuestionBasic(BaseModel):
    """题目基本信息"""
    id: int
    title: str
    level: int | None = None
    question_type: str

    class Config:
        from_attributes = True


# ============ ExamPaper Schemas ============

class ExamPaperBase(BaseModel):
    title: str
    level: str  # A/B/C/D/E/F
    total_questions: int = 10
    description: str | None = None
    paper_type: str = "daily"  # daily/mock/topic


class ExamPaperCreate(ExamPaperBase):
    pass


class ExamPaperUpdate(BaseModel):
    title: str | None = None
    level: str | None = None
    total_questions: int | None = None
    description: str | None = None
    paper_type: str | None = None


class ExamPaperResponse(BaseModel):
    id: int
    title: str
    level: str
    total_questions: int
    description: str | None
    paper_type: str
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class ExamPaperWithQuestions(ExamPaperResponse):
    """考卷详情，包含题目列表"""
    questions: list["ExamPaperQuestionResponse"] = []


# ============ ExamPaperQuestion Schemas ============

class ExamPaperQuestionBase(BaseModel):
    question_id: int
    sort: int = 1


class ExamPaperQuestionCreate(ExamPaperQuestionBase):
    pass


class ExamPaperQuestionUpdate(BaseModel):
    sort: int | None = None


class ExamPaperQuestionResponse(BaseModel):
    id: int
    exam_paper_id: int
    question_id: int
    sort: int
    question: QuestionBasic | None = None  # 包含题目详情

    class Config:
        from_attributes = True


# 更新前向引用
ExamPaperWithQuestions.model_rebuild()