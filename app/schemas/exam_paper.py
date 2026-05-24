"""
ExamPaper schemas - 考卷相关数据结构
"""
from datetime import datetime
from pydantic import BaseModel

from app.schemas.question import BaseQuestionSchema


# ============ Question Basic Schema ============

class QuestionBasic(BaseQuestionSchema):
    """题目基本信息（用于考卷详情）"""
    id: int
    title: str
    topic_id: int | None = None
    difficulty_level: int | None = None
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
    difficulty_level: int = 1  # 难度等级 1-6
    total_questions: int = 10
    description: str | None = None
    paper_type: str = "daily"  # daily/mock/topic/past
    status: str = "published"  # published/unpublished


class ExamPaperCreate(ExamPaperBase):
    pass


class GeneratePaperRequest(BaseModel):
    """生成考卷请求"""
    mode: str = "manual"  # manual | smart
    topic_ids: list[int] | None = None
    difficulty_level: int = 3
    question_count: int = 24
    title: str | None = None
    include_wrong: bool = False
    include_favorite: bool = False


class TopicQuestionCount(BaseModel):
    """专题题目数量"""
    topic_id: int
    topic_title: str
    count: int


class GeneratePaperResponse(BaseModel):
    """生成考卷响应"""
    exam_paper_id: int
    title: str
    total_questions: int
    topic_question_counts: list[TopicQuestionCount] = []


class GeneratePdfResponse(BaseModel):
    """生成 PDF 响应"""
    exam_paper_id: int
    file_path: str


class DeletePaperResponse(BaseModel):
    """删除考卷响应"""
    ok: bool


class ExamPaperUpdate(BaseModel):
    title: str | None = None
    difficulty_level: int | None = None
    total_questions: int | None = None
    description: str | None = None
    paper_type: str | None = None
    status: str | None = None


class ExamPaperResponse(BaseModel):
    id: int
    title: str
    difficulty_level: int
    total_questions: int
    description: str | None
    paper_type: str
    is_new: bool = False
    file_path: str | None = None
    status: str = "published"
    user_completed: bool = False
    user_score: int | None = None
    user_id: int | None = None
    generation_config: dict | None = None
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
    correct_answers_summary: dict[int, str] | None = None


class AnswerSheetItem(BaseQuestionSchema):
    """答题卡单项"""
    index: int
    question_id: int
    user_answer: str
    correct_answer: str
    is_correct: bool
    # 题目详情（可选）
    question_title: str | None = None
    question_content: dict | None = None
    question_options: list[dict] | None = None
    question_explanation: dict | None = None


class ExamPaperTestReport(BaseModel):
    """测试报告详情（包含完整答题卡）"""
    id: int
    user_id: int
    exam_paper_id: int
    exam_paper_title: str | None = None
    score: int
    correct_count: int
    wrong_count: int
    total_questions: int
    time_spent: int
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    # 答题卡数据
    answer_sheet: list[AnswerSheetItem] = []


class ExamPaperListResponse(BaseModel):
    """考卷列表（分页）"""
    total: int
    page: int
    page_size: int
    items: list[ExamPaperResponse]


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


class UserWrongQuestion(BaseQuestionSchema):
    """用户错题详情"""
    question_id: int
    question_title: str | None = None
    correct_answer: str
    wrong_count: int  # 答错次数
    last_wrong_at: datetime | None = None
    question: QuestionBasic | None = None