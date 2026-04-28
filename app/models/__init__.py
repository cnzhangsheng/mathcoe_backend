"""
Models module - SQLAlchemy ORM models
"""
from app.models.base import Base, BaseModel
from app.models.admin import Admin
from app.models.user import User
from app.models.topic import Topic
from app.models.question import Question
from app.models.exam_paper import ExamPaper, ExamPaperQuestion
from app.models.exam_paper_test import ExamPaperTest
from app.models.exam_paper_test_answer import TestAnswerRecord
from app.models.user_progress import UserProgress
from app.models.practice_record import PracticeRecord
from app.models.favorite import Favorite, WrongQuestion
from app.models.like import Like

__all__ = [
    "Base",
    "BaseModel",
    "Admin",
    "User",
    "Topic",
    "Question",
    "ExamPaper",
    "ExamPaperQuestion",
    "ExamPaperTest",
    "TestAnswerRecord",
    "UserProgress",
    "PracticeRecord",
    "Favorite",
    "WrongQuestion",
    "Like",
]