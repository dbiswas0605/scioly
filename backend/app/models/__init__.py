"""Import every model module so Base.metadata is fully populated.

This module must be imported (e.g. by Alembic's env.py) before any
metadata-driven operation (autogenerate, create_all, etc.) so that all
tables and their relationships are registered on the shared Base.
"""
from app.models.subject import Subject  # noqa: F401
from app.models.question_paper import QuestionPaper  # noqa: F401
from app.models.question import Question  # noqa: F401
from app.models.question_option import QuestionOption  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.exam_attempt import ExamAttempt  # noqa: F401
from app.models.attempt_answer import AttemptAnswer  # noqa: F401
from app.models.llm_provider import LlmProvider  # noqa: F401
from app.models.app_setting import AppSetting  # noqa: F401

__all__ = [
    "Subject",
    "QuestionPaper",
    "Question",
    "QuestionOption",
    "Student",
    "ExamAttempt",
    "AttemptAnswer",
    "LlmProvider",
    "AppSetting",
]
