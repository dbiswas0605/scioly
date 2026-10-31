"""Database engine, session factory, and FastAPI dependency."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

bootstrap_engine = create_engine(settings.database_url, pool_pre_ping=True)
active_engine = bootstrap_engine

BootstrapSessionLocal = sessionmaker(
    bind=bootstrap_engine, autocommit=False, autoflush=False
)
SessionLocal = sessionmaker(bind=active_engine, autocommit=False, autoflush=False)


def switch_active_database(engine: Engine) -> None:
    """Route new application sessions to a validated database engine."""
    global active_engine
    previous_engine = active_engine
    active_engine = engine
    SessionLocal.configure(bind=active_engine)
    if previous_engine is not bootstrap_engine and previous_engine is not engine:
        previous_engine.dispose()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a DB session, closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
