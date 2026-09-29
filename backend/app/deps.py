"""Shared FastAPI dependencies. Currently just re-exports the DB session dep."""
from __future__ import annotations

from app.db.session import get_db

__all__ = ["get_db"]
