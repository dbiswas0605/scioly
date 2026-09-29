"""Database engine, session factory, and FastAPI dependency."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a DB session, closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
