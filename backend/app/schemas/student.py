"""Pydantic schemas for the Student resource."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    created_at: datetime
