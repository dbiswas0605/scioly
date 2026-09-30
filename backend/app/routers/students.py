"""Routes for listing and creating Students."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import exam_attempts as attempts_crud
from app.crud import students as students_crud
from app.deps import get_db
from app.schemas.exam_attempt import ExamAttemptRead
from app.schemas.student import StudentCreate, StudentRead

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentRead])
def list_students(db: Session = Depends(get_db)) -> list[StudentRead]:
    return list(students_crud.list_students(db))


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate, db: Session = Depends(get_db)
) -> StudentRead:
    existing = students_crud.get_student_by_name(db, payload.display_name)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this display name already exists.",
        )
    return students_crud.create_student(db, display_name=payload.display_name)


@router.get("/{student_id}/attempts", response_model=list[ExamAttemptRead])
def list_student_attempts(
    student_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[ExamAttemptRead]:
    """All of this student's attempts across every paper — used to show
    "already taken" + score on Practice tiles."""
    return list(attempts_crud.list_attempts_for_student(db, student_id))
