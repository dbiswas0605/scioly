"""Pydantic schemas for taking and reviewing exam attempts.

Scoring policy: only `mcq` questions are auto-graded. `short_answer`
answers are recorded (for the parent/admin to read later) but don't count
toward `max_score`/`correct_count` — there's no free-text grading yet.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.question import QuestionOptionRead, QuestionType

AttemptStatus = Literal["in_progress", "submitted", "timed_out", "abandoned"]


class ExamAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    paper_id: uuid.UUID
    attempt_number: int
    status: AttemptStatus
    started_at: datetime
    submitted_at: datetime | None
    duration_minutes_snapshot: int
    score: Decimal | None
    max_score: Decimal | None
    correct_count: int | None
    total_questions: int | None
    created_at: datetime


class ExamAttemptStart(BaseModel):
    student_name: str


# --- Taking the exam: questions with correct answers/explanations hidden ---


class ExamQuestionOptionPublic(BaseModel):
    id: uuid.UUID
    option_label: str
    option_text: str | None
    has_image: bool
    display_order: int


class ExamQuestionPublic(BaseModel):
    id: uuid.UUID
    question_number: int
    question_type: QuestionType
    prompt_text: str
    has_prompt_image: bool
    points: Decimal
    options: list[ExamQuestionOptionPublic]


class ExamSessionRead(ExamAttemptRead):
    paper_title: str
    questions: list[ExamQuestionPublic]


# --- Submitting answers ---


class AnswerInput(BaseModel):
    question_id: uuid.UUID
    selected_option_id: uuid.UUID | None = None
    short_answer_text: str | None = None


class AttemptSubmit(BaseModel):
    answers: list[AnswerInput] = []
    reason: Literal["submitted", "timed_out"] = "submitted"


# --- Reviewing a finished attempt: everything revealed ---


class AnswerReviewRead(BaseModel):
    question_id: uuid.UUID
    question_number: int
    question_type: QuestionType
    prompt_text: str
    explanation_text: str | None
    points: Decimal
    options: list[QuestionOptionRead]
    selected_option_id: uuid.UUID | None
    short_answer_text: str | None
    short_answer_expected: str | None
    is_correct: bool | None


class AttemptReviewRead(ExamAttemptRead):
    paper_title: str
    answers: list[AnswerReviewRead]
