"""Pydantic schemas for the Parent/Teacher reports dashboard — read-only
aggregations over exam_attempts, not a new persisted resource."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.exam_attempt import AttemptStatus


class AttemptPoint(BaseModel):
    attempt_id: uuid.UUID
    attempt_number: int
    status: AttemptStatus
    score: Decimal | None
    max_score: Decimal | None
    percent: float | None
    started_at: datetime
    submitted_at: datetime | None


class StudentPaperReport(BaseModel):
    student_id: uuid.UUID
    student_name: str
    paper_id: uuid.UUID
    paper_title: str
    subject_name: str
    attempts: list[AttemptPoint]


class StudentOverview(BaseModel):
    student_id: uuid.UUID
    student_name: str
    total_attempts: int
    papers_attempted: int
    average_percent: float | None
    last_activity: datetime | None
