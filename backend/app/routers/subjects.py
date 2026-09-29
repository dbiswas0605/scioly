"""Routes for listing and creating Subjects."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import subjects as subjects_crud
from app.deps import get_db
from app.schemas.subject import SubjectCreate, SubjectRead

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[SubjectRead])
def list_subjects(db: Session = Depends(get_db)) -> list[SubjectRead]:
    return list(subjects_crud.list_subjects(db))


@router.post("", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate, db: Session = Depends(get_db)
) -> SubjectRead:
    existing = subjects_crud.get_subject_by_name(db, payload.name)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A subject with this name already exists.",
        )
    return subjects_crud.create_subject(db, name=payload.name)
