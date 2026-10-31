"""Import every model module so Base.metadata is fully populated.

This module must be imported (e.g. by Alembic's env.py) before any
metadata-driven operation (autogenerate, create_all, etc.) so that all
tables and their relationships are registered on the shared Base.
"""
from app.models.app_setting import AppSetting
from app.models.attempt_answer import AttemptAnswer
from app.models.database_connection import DatabaseConnection
from app.models.exam_attempt import ExamAttempt
from app.models.llm_provider import LlmProvider
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.question_paper import QuestionPaper
from app.models.student import Student
from app.models.subject import Subject

__all__ = [
    "AppSetting",
    "AttemptAnswer",
    "DatabaseConnection",
    "ExamAttempt",
    "LlmProvider",
    "Question",
    "QuestionOption",
    "QuestionPaper",
    "Student",
    "Subject",
]
