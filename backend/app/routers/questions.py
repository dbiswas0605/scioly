"""Question listing and per-question editing for the upload review
workflow. A parent/teacher edits/confirms each parsed question here before
the paper can be published."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import question_papers as papers_crud
from app.crud import questions as questions_crud
from app.deps import get_db
from app.schemas.question import QuestionOptionRead, QuestionRead, QuestionUpdate

router = APIRouter(prefix="/papers", tags=["questions"])


def _to_question_read(question) -> QuestionRead:
    options = [
        QuestionOptionRead(
            id=option.id,
            question_id=option.question_id,
            option_label=option.option_label,
            option_text=option.option_text,
            has_image=option.option_image is not None,
            is_correct=option.is_correct,
            display_order=option.display_order,
        )
        for option in sorted(question.options, key=lambda o: o.display_order)
    ]
    base = QuestionRead.model_validate(question).model_dump(exclude={"options"})
    return QuestionRead(**base, options=options)


@router.get("/{paper_id}/questions", response_model=list[QuestionRead])
def list_questions(
    paper_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[QuestionRead]:
    paper = papers_crud.get_paper_by_id(db, paper_id)
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question paper not found."
        )

    questions = questions_crud.list_questions_for_paper(db, paper_id)
    return [_to_question_read(question) for question in questions]


@router.patch("/{paper_id}/questions/{question_id}", response_model=QuestionRead)
def update_question(
    paper_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
) -> QuestionRead:
    """Save a parent's edits to a parsed question and mark it reviewed."""
    question = questions_crud.get_question_for_paper(db, paper_id, question_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found."
        )

    data = payload.model_dump()
    options = data.pop("options")
    if data["question_type"] == "short_answer":
        options = []
    elif sum(1 for option in options if option["is_correct"]) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mark exactly one option as correct before saving this question.",
        )
    data["options"] = options

    question = questions_crud.update_question(db, question, data)
    return _to_question_read(question)
