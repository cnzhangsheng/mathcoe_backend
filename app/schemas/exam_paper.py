"""
ExamPaper schemas - 考卷相关数据结构
"""
from datetime import datetime
from pydantic import BaseModel


# ============ Question Basic Schema ============

class QuestionBasic(BaseModel):
    """题目基本信息（用于考卷详情）"""
    id: int
    title: str
    level: int | None = None
    question_type: str
    options: list[dict] | None = None
    content: dict | None = None
    answer: str | None = None
    explanation: dict | None = None

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


# ============ ExamPaperTest Schemas ============

class ExamPaperTestStart(BaseModel):
    """开始测试请求"""
    exam_paper_id: int


class ExamPaperTestAnswer(BaseModel):
    """提交单题答案"""
    question_index: int  # 题目序号（1-N）
    user_answer: str  # 用户答案 A/B/C/D


class ExamPaperTestSubmit(BaseModel):
    """完成测试请求"""
    answers: dict[int, str]  # 所有答案 {1: "A", 2: "B"}
    time_spent: int  # 用时（秒）


class ExamPaperTestResponse(BaseModel):
    """测试记录响应"""
    id: int
    user_id: int
    exam_paper_id: int
    exam_paper_title: str | None = None
    score: int | None = None
    correct_count: int | None = None
    total_questions: int
    time_spent: int | None = None
    started_at: datetime
    finished_at: datetime | None = None
    status: str

    class Config:
        from_attributes = True


class ExamPaperTestDetail(ExamPaperTestResponse):
    """测试记录详情"""
    correct_answers_summary: dict[int, str] | None = None  # 正确答案汇总（仅用于展示）


class ExamPaperTestList(BaseModel):
    """测试记录列表"""
    total: int
    items: list[ExamPaperTestResponse]


# ============ ExamPaperTestAnswer Schemas ============

class ExamPaperTestAnswerResponse(BaseModel):
    """答题记录响应"""
    id: int
    test_id: int
    user_id: int
    exam_paper_id: int
    question_index: int
    question_id: int
    user_answer: str
    correct_answer: str
    is_correct: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WrongQuestionStats(BaseModel):
    """错题统计"""
    question_id: int
    wrong_count: int  # 答错次数
    correct_count: int  # 答对次数
    total_count: int  # 总答题次数
    wrong_rate: float  # 错误率（百分比）


class UserWrongQuestion(BaseModel):
    """用户错题详情"""
    question_id: int
    question_title: str | None = None
    correct_answer: str
    wrong_count: int  # 答错次数
    last_wrong_at: datetime | None = None
    question: QuestionBasic | None = None