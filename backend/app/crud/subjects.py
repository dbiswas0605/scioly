"""CRUD helpers for the Subject resource."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subject import Subject


def list_subjects(db: Session) -> list[Subject]:
    return list(db.scalars(select(Subject).order_by(Subject.name)))


def get_subject_by_id(db: Session, subject_id: uuid.UUID) -> Subject | None:
    return db.get(Subject, subject_id)


def get_subject_by_name(db: Session, name: str) -> Subject | None:
    return db.scalars(
        select(Subject).where(Subject.name.ilike(name))
    ).first()


def create_subject(db: Session, *, name: str) -> Subject:
    subject = Subject(name=name)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject
