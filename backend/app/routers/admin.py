"""Admin routes: LLM provider configuration and generic app settings.

All admin settings are DB-driven per project conventions — nothing here is
read from environment variables at request time.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import admin_settings as admin_crud
from app.deps import get_db
from app.schemas.admin_setting import (
    AppSettingRead,
    AppSettingUpdate,
    LlmProviderRead,
    LlmProviderTestResult,
    LlmProviderUpdate,
)
from app.services.llm.dispatcher import test_provider_connection

router = APIRouter(prefix="/admin", tags=["admin"])


def _to_provider_read(provider) -> LlmProviderRead:
    data = LlmProviderRead.model_validate(provider).model_dump()
    data["has_api_key"] = bool(provider.api_key)
    return LlmProviderRead(**data)


@router.get("/llm-providers", response_model=list[LlmProviderRead])
def list_llm_providers(db: Session = Depends(get_db)) -> list[LlmProviderRead]:
    providers = admin_crud.list_llm_providers(db)
    return [_to_provider_read(p) for p in providers]


@router.put("/llm-providers/{provider_id}", response_model=LlmProviderRead)
def update_llm_provider(
    provider_id: uuid.UUID,
    payload: LlmProviderUpdate,
    db: Session = Depends(get_db),
) -> LlmProviderRead:
    provider = admin_crud.get_llm_provider(db, provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LLM provider not found."
        )
    updates = payload.model_dump(exclude_unset=True)
    provider = admin_crud.update_llm_provider(db, provider, updates)
    return _to_provider_read(provider)


@router.post("/llm-providers/{provider_id}/test", response_model=LlmProviderTestResult)
def test_llm_provider(
    provider_id: uuid.UUID, db: Session = Depends(get_db)
) -> LlmProviderTestResult:
    """Verify a provider actually works — checks API-key auth for cloud
    providers, or plain connectivity for local ones — without spending
    tokens on a real completion. Returns ok=false (not a 4xx/5xx) for a bad
    key or unreachable server; that's an expected test outcome, not a
    server error."""
    provider = admin_crud.get_llm_provider(db, provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LLM provider not found."
        )

    result = test_provider_connection(provider)
    return LlmProviderTestResult(**result)


@router.get("/settings", response_model=list[AppSettingRead])
def list_settings(db: Session = Depends(get_db)) -> list[AppSettingRead]:
    return list(admin_crud.list_app_settings(db))


@router.put("/settings/{key}", response_model=AppSettingRead)
def upsert_setting(
    key: str, payload: AppSettingUpdate, db: Session = Depends(get_db)
) -> AppSettingRead:
    updates = payload.model_dump(exclude_unset=True)
    return admin_crud.upsert_app_setting(db, key, updates)
