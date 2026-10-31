"""Schemas for selecting the PostgreSQL database used by the application."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DatabaseTableSummary(BaseModel):
    name: str
    record_count: int


class DatabaseConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    host: str
    port: int
    database: str
    username: str
    has_password: bool
    updated_at: datetime | None = None
    is_active: bool
    tables: list[DatabaseTableSummary] = Field(default_factory=list)
    total_records: int = 0


class DatabaseConnectionUpdate(BaseModel):
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    database: str = Field(min_length=1, max_length=255)
    username: str = Field(min_length=1, max_length=255)
    password: str | None = None
