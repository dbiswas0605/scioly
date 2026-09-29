"""Health-check endpoint used by uptime checks and local dev sanity checks."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.deps import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "error", "db": "error"}
    return {"status": "ok", "db": "ok"}
