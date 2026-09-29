"""CRUD helpers for the Student resource."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.student import Student


def list_students(db: Session) -> list[Student]:
    return list(db.scalars(select(Student).order_by(Student.display_name)))


def get_student_by_name(db: Session, display_name: str) -> Student | None:
    return db.scalars(
        select(Student).where(Student.display_name.ilike(display_name))
    ).first()


def create_student(db: Session, *, display_name: str) -> Student:
    student = Student(display_name=display_name)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student
