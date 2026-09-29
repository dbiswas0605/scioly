"""Pydantic schemas for the Question and QuestionOption resources."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

QuestionType = Literal["mcq", "short_answer"]


class QuestionOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    option_label: str
    option_text: str | None
    has_image: bool = False
    is_correct: bool
    display_order: int


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    paper_id: uuid.UUID
    question_number: int
    question_type: QuestionType
    prompt_text: str
    explanation_text: str | None
    short_answer_expected: str | None
    points: Decimal
    llm_suggested_answer: str | None
    is_reviewed: bool
    created_at: datetime
    updated_at: datetime
    options: list[QuestionOptionRead] = []


class QuestionOptionInput(BaseModel):
    option_label: str
    option_text: str | None = None
    is_correct: bool = False
    display_order: int = 0


class QuestionUpdate(BaseModel):
    """Body for PATCH /papers/{paper_id}/questions/{question_id}. Saving
    always marks the question reviewed — this is the parent's confirmation
    step in the upload review workflow.
    """

    question_type: QuestionType
    prompt_text: str
    explanation_text: str | None = None
    short_answer_expected: str | None = None
    points: Decimal = Decimal("1.0")
    options: list[QuestionOptionInput] = []
