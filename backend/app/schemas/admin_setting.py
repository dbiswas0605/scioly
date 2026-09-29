"""Pydantic schemas for admin-managed LLM providers and app settings."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

SettingValueType = Literal["string", "integer", "boolean", "json"]


class LlmProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider_key: str
    display_name: str
    has_api_key: bool = False
    base_url: str | None
    model_name: str
    is_enabled: bool
    priority: int
    extra_config: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class LlmProviderTestResult(BaseModel):
    ok: bool
    message: str
    model_checked: str | None = None
    model_available: bool | None = None


class LlmProviderUpdate(BaseModel):
    display_name: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model_name: str | None = None
    is_enabled: bool | None = None
    priority: int | None = None
    extra_config: dict[str, Any] | None = None


class AppSettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str | None
    value_type: SettingValueType
    description: str | None
    updated_at: datetime


class AppSettingUpdate(BaseModel):
    value: str | None = None
    value_type: SettingValueType | None = None
    description: str | None = None
