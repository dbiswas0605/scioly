"""Tests for the live paper parsing progress stream."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.routers import papers as papers_router


class _SessionContext:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


def test_parse_stream_reports_missing_paper(client, monkeypatch) -> None:
    monkeypatch.setattr(papers_router, "SessionLocal", _SessionContext)
    monkeypatch.setattr(
        papers_router.papers_crud, "get_paper_by_id", lambda _db, _paper_id: None
    )

    response = client.post(f"/api/papers/{uuid.uuid4()}/parse/stream")

    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.splitlines()]
    assert events[0] == {
        "type": "log",
        "message": "Opening the stored source document from PostgreSQL.",
    }
    assert events[1] == {"type": "error", "message": "Question paper not found."}


def test_parse_stream_returns_questions_and_paper(client, monkeypatch) -> None:
    paper_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    paper = SimpleNamespace(
        id=paper_id,
        subject_id=uuid.uuid4(),
        title="Sample paper",
        description=None,
        source_filename="sample.pdf",
        source_content_type="application/pdf",
        source_file=b"pdf data",
        source_file_size_bytes=8,
        status="draft",
        default_duration_minutes=30,
        total_questions=0,
        created_by=None,
        created_at=now,
        updated_at=now,
    )

    def fake_parser(_db, _paper, progress):
        progress("Reading questions from the model response.")
        return [{"question_number": 1}]

    def update_paper(_db, current_paper, *, status, total_questions):
        current_paper.status = status
        current_paper.total_questions = total_questions
        return current_paper

    monkeypatch.setattr(papers_router, "SessionLocal", _SessionContext)
    monkeypatch.setattr(
        papers_router.papers_crud,
        "get_paper_by_id",
        lambda _db, _paper_id: paper,
    )
    monkeypatch.setattr(papers_router, "parse_paper_with_llm", fake_parser)
    monkeypatch.setattr(
        papers_router.questions_crud,
        "replace_questions_for_paper",
        lambda _db, _paper_id, _questions: None,
    )
    monkeypatch.setattr(
        papers_router.papers_crud,
        "set_status_and_question_count",
        update_paper,
    )

    response = client.post(f"/api/papers/{paper_id}/parse/stream")

    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.splitlines()]
    assert any(
        event.get("message") == "Reading questions from the model response."
        for event in events
    )
    assert events[-1]["type"] == "complete"
    assert events[-1]["paper"]["id"] == str(paper_id)
    assert events[-1]["paper"]["total_questions"] == 1
