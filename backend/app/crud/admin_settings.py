"""CRUD helpers for admin-managed LLM providers and app settings."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting
from app.models.llm_provider import LlmProvider


def list_llm_providers(db: Session) -> list[LlmProvider]:
    return list(
        db.scalars(
            select(LlmProvider).order_by(
                LlmProvider.priority, LlmProvider.provider_key
            )
        )
    )


def get_llm_provider(db: Session, provider_id: uuid.UUID) -> LlmProvider | None:
    return db.get(LlmProvider, provider_id)


def list_enabled_llm_providers(db: Session) -> list[LlmProvider]:
    """Enabled providers in the order `dispatcher.py` should try them —
    ascending priority (lower number first)."""
    return list(
        db.scalars(
            select(LlmProvider)
            .where(LlmProvider.is_enabled.is_(True))
            .order_by(LlmProvider.priority, LlmProvider.provider_key)
        )
    )


def update_llm_provider(
    db: Session, provider: LlmProvider, updates: dict[str, Any]
) -> LlmProvider:
    """Apply updates to a provider. `updates` should only contain fields the
    caller explicitly provided (e.g. via `model_dump(exclude_unset=True)`)."""
    for field, value in updates.items():
        setattr(provider, field, value)

    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


DEFAULT_EXAM_DURATION_KEY = "default_exam_duration_minutes"
DEFAULT_EXAM_DURATION_MINUTES = 30


def list_app_settings(db: Session) -> list[AppSetting]:
    return list(db.scalars(select(AppSetting).order_by(AppSetting.key)))


def get_default_exam_duration_minutes(db: Session) -> int:
    """The admin-configurable default timer (minutes) applied to newly
    uploaded papers. Falls back to 30 if the setting is missing or somehow
    not a valid integer, rather than failing an upload over it."""
    setting = db.get(AppSetting, DEFAULT_EXAM_DURATION_KEY)
    if setting is None or setting.value is None:
        return DEFAULT_EXAM_DURATION_MINUTES
    try:
        return int(setting.value)
    except ValueError:
        return DEFAULT_EXAM_DURATION_MINUTES


def get_app_setting(db: Session, key: str) -> AppSetting | None:
    return db.get(AppSetting, key)


def upsert_app_setting(
    db: Session, key: str, updates: dict[str, Any]
) -> AppSetting:
    """Insert or update an app_settings row. `updates` should only contain
    fields the caller explicitly provided (e.g. via
    `model_dump(exclude_unset=True)`), so omitted fields are left untouched
    on an existing row.
    """
    setting = db.get(AppSetting, key)
    if setting is None:
        setting = AppSetting(
            key=key,
            value=updates.get("value"),
            value_type=updates.get("value_type") or "string",
            description=updates.get("description"),
        )
        db.add(setting)
    else:
        for field, value in updates.items():
            setattr(setting, field, value)
    db.commit()
    db.refresh(setting)
    return setting
