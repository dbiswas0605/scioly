"""Pydantic schemas for the Subject resource."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class SubjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
