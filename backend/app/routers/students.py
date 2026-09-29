"""Routes for listing and creating Students."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import students as students_crud
from app.deps import get_db
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
