"""Pydantic schemas for the QuestionPaper resource.

Upload is handled via multipart form fields directly in the router, so no
QuestionPaperCreate schema is needed. The read schema deliberately omits the
raw source_file bytes — only metadata is ever returned over the API.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PaperStatus = Literal["draft", "pending_review", "published", "archived"]


class QuestionPaperRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: uuid.UUID
    title: str
    description: str | None
    source_filename: str
    source_content_type: str
    source_file_size_bytes: int
    status: PaperStatus
    default_duration_minutes: int
    total_questions: int
    created_by: str | None
    created_at: datetime
    updated_at: datetime


class QuestionPaperWithSubjectRead(QuestionPaperRead):
    subject_name: str


class QuestionPaperDurationUpdate(BaseModel):
    default_duration_minutes: int = Field(gt=0, le=480)
