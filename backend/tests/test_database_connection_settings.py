from __future__ import annotations

from sqlalchemy import create_engine, text

from app.routers import admin as admin_router
from app.services.database_connection import (
    build_connection_engine,
    get_table_record_counts,
)


def test_database_settings_api_never_returns_password(client, monkeypatch) -> None:
    saved_settings = {
        "host": "192.168.1.188",
        "port": 5433,
        "database": "scioly",
        "username": "scioly",
        "has_password": True,
        "updated_at": None,
        "is_active": True,
    }
    monkeypatch.setattr(
        admin_router.database_connection_service,
        "active_connection_details",
        lambda: saved_settings,
    )
    submitted: dict[str, object] = {}

    def apply_connection(**settings) -> tuple[list[dict[str, object]], int]:
        submitted.update(settings)
        return [{"name": "questions", "record_count": 4}], 4

    monkeypatch.setattr(
        admin_router.database_connection_service,
        "apply_connection",
        apply_connection,
    )

    response = client.put(
        "/api/admin/database",
        json={
            "host": "192.168.1.188",
            "port": 5433,
            "database": "scioly",
            "username": "scioly",
            "password": "do-not-return-this",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        **saved_settings,
        "tables": [{"name": "questions", "record_count": 4}],
        "total_records": 4,
    }
    assert "password" not in response.json()
    assert submitted["password"] == "do-not-return-this"


def test_database_url_escapes_password_and_hides_it_when_rendered() -> None:
    engine = build_connection_engine(
        host="192.168.1.188",
        port=5433,
        database="scioly",
        username="scioly",
        password="a:/?secret",
    )
    try:
        assert engine.url.password == "a:/?secret"
        assert "a:/?secret" not in engine.url.render_as_string(hide_password=True)
    finally:
        engine.dispose()


def test_table_record_counts_lists_tables_and_totals_rows() -> None:
    engine = create_engine("sqlite:///:memory:")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE questions (id INTEGER PRIMARY KEY)"))
            connection.execute(text("CREATE TABLE students (id INTEGER PRIMARY KEY)"))
            connection.execute(text("INSERT INTO questions (id) VALUES (1), (2), (3)"))
            connection.execute(text("INSERT INTO students (id) VALUES (1), (2)"))

        tables, total_records = get_table_record_counts(engine)

        assert tables == [
            {"name": "questions", "record_count": 3},
            {"name": "students", "record_count": 2},
        ]
        assert total_records == 5
    finally:
        engine.dispose()
