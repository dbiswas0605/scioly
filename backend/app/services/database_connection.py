"""Load, validate, and apply the configured application database."""
from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.util.exc import CommandError
from sqlalchemy import (
    URL,
    Engine,
    MetaData,
    Table,
    create_engine,
    func,
    inspect,
    select,
    text,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import session as db_session
from app.models.database_connection import DatabaseConnection

logger = logging.getLogger(__name__)
_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def get_saved_connection() -> DatabaseConnection | None:
    with db_session.BootstrapSessionLocal() as db:
        return db.get(DatabaseConnection, 1)


def build_connection_engine(
    *,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
) -> Engine:
    url = URL.create(
        "postgresql+psycopg",
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    return create_engine(url, pool_pre_ping=True)


def _initialize_database(engine: Engine) -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    alembic_config = Config(str(_BACKEND_ROOT / "alembic.ini"))
    with engine.begin() as connection:
        alembic_config.attributes["connection"] = connection
        command.upgrade(alembic_config, "head")

    from scripts.seed import (
        seed_app_settings,
        seed_demo_student,
        seed_llm_providers,
        seed_subjects,
    )

    with Session(engine) as db:
        seed_subjects(db)
        seed_demo_student(db)
        seed_app_settings(db)
        seed_llm_providers(db)
        db.commit()


def get_table_record_counts(engine: Engine) -> tuple[list[dict[str, object]], int]:
    tables: list[dict[str, object]] = []
    total_records = 0
    metadata = MetaData()
    with engine.connect() as connection:
        schema = "public" if connection.dialect.name == "postgresql" else None
        for table_name in sorted(inspect(connection).get_table_names(schema=schema)):
            table = Table(
                table_name,
                metadata,
                schema=schema,
                autoload_with=connection,
            )
            record_count = connection.scalar(
                select(func.count()).select_from(table)
            )
            count = int(record_count or 0)
            tables.append({"name": table_name, "record_count": count})
            total_records += count
    return tables, total_records


def apply_connection(
    *,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str | None,
) -> tuple[list[dict[str, object]], int]:
    saved = get_saved_connection()
    effective_password = password or (saved.password if saved is not None else None)
    if not effective_password:
        raise ValueError("A database password is required.")

    engine = build_connection_engine(
        host=host,
        port=port,
        database=database,
        username=username,
        password=effective_password,
    )
    try:
        _initialize_database(engine)
        table_counts = get_table_record_counts(engine)
    except Exception:
        engine.dispose()
        raise

    with db_session.BootstrapSessionLocal() as db:
        db.merge(
            DatabaseConnection(
                id=1,
                host=host,
                port=port,
                database=database,
                username=username,
                password=effective_password,
            )
        )
        db.commit()

    db_session.switch_active_database(engine)
    return table_counts


def apply_saved_connection_on_startup() -> None:
    saved = get_saved_connection()
    if saved is None:
        return

    engine = build_connection_engine(
        host=saved.host,
        port=saved.port,
        database=saved.database,
        username=saved.username,
        password=saved.password,
    )
    try:
        _initialize_database(engine)
    except Exception as exc:
        engine.dispose()
        logger.error(
            "Could not initialize the configured application database (%s).",
            type(exc).__name__,
        )
        raise RuntimeError(
            "Could not initialize the configured application database. "
            "Check the connection settings in Admin."
        ) from exc

    db_session.switch_active_database(engine)


def active_connection_details() -> dict[str, object]:
    saved = get_saved_connection()
    if saved is not None:
        return {
            "host": saved.host,
            "port": saved.port,
            "database": saved.database,
            "username": saved.username,
            "has_password": bool(saved.password),
            "updated_at": saved.updated_at,
            "is_active": True,
        }

    url = db_session.active_engine.url
    return {
        "host": url.host or "",
        "port": url.port or 5432,
        "database": url.database or "",
        "username": url.username or "",
        "has_password": False,
        "updated_at": None,
        "is_active": True,
    }


DatabaseConfigurationError = (SQLAlchemyError, CommandError, OSError, ValueError)
