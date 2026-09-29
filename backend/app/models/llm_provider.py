"""LlmProvider model — configuration for an LLM backend (Anthropic, OpenAI,
Ollama, or MLX via an OpenAI-compatible local server).

Any number of providers can be enabled at once — `dispatcher.py` tries them
in ascending `priority` order (lower number = tried first) and falls back
to the next one if a provider fails, so e.g. a local provider can be given
priority over a cloud one without a single exclusive "active" flag.
"""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LlmProvider(Base, TimestampMixin):
    __tablename__ = "llm_providers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider_key: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="100"
    )
    extra_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
