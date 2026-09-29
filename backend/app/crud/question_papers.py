"""CRUD helpers for the QuestionPaper resource."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.question_paper import QuestionPaper
from app.models.subject import Subject


def list_papers(db: Session) -> list[tuple[QuestionPaper, str]]:
    """Return (paper, subject_name) tuples, newest first."""
    rows = db.execute(
        select(QuestionPaper, Subject.name)
        .join(Subject, QuestionPaper.subject_id == Subject.id)
        .order_by(QuestionPaper.created_at.desc())
    ).all()
    return [(paper, subject_name) for paper, subject_name in rows]


def get_paper_by_id(db: Session, paper_id: uuid.UUID) -> QuestionPaper | None:
    return db.get(QuestionPaper, paper_id, options=[joinedload(QuestionPaper.subject)])


def create_paper(
    db: Session,
    *,
    subject_id: uuid.UUID,
    title: str,
    source_filename: str,
    source_content_type: str,
    source_file: bytes,
    description: str | None = None,
    created_by: str | None = None,
) -> QuestionPaper:
    paper = QuestionPaper(
        subject_id=subject_id,
        title=title,
        description=description,
        source_filename=source_filename,
        source_content_type=source_content_type,
        source_file=source_file,
        source_file_size_bytes=len(source_file),
        status="draft",
        created_by=created_by,
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return paper


def set_status_and_question_count(
    db: Session, paper: QuestionPaper, *, status: str, total_questions: int
) -> QuestionPaper:
    paper.status = status
    paper.total_questions = total_questions
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return paper


def set_status(db: Session, paper: QuestionPaper, status: str) -> QuestionPaper:
    paper.status = status
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return paper


def delete_paper(db: Session, paper: QuestionPaper) -> None:
    """Deletes the paper along with its questions/options and any student
    exam_attempts/attempt_answers (all cascade at the DB level via FK
    ondelete="CASCADE"), regardless of the paper's status."""
    db.delete(paper)
    db.commit()
