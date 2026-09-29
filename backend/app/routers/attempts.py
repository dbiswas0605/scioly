"""Exam-attempt routes: starting a timed attempt, submitting answers
(auto-scored for mcq), and reviewing a finished attempt with everything
revealed.

Two routers live here: `router` for attempt-id-scoped routes
(/attempts/{id}...) and `paper_router` for paper-scoped ones
(/papers/{paper_id}/attempts) — mirroring how questions.py keeps
paper-scoped routes under /papers.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import exam_attempts as attempts_crud
from app.crud import question_papers as papers_crud
from app.crud import questions as questions_crud
from app.crud import students as students_crud
from app.deps import get_db
from app.models.attempt_answer import AttemptAnswer
from app.models.exam_attempt import ExamAttempt
from app.models.question import Question
from app.models.question_paper import QuestionPaper
from app.schemas.exam_attempt import (
    AnswerReviewRead,
    AttemptReviewRead,
    AttemptSubmit,
    ExamAttemptRead,
    ExamAttemptStart,
    ExamQuestionOptionPublic,
    ExamQuestionPublic,
    ExamSessionRead,
)
from app.schemas.question import QuestionOptionRead

router = APIRouter(prefix="/attempts", tags=["attempts"])
paper_router = APIRouter(prefix="/papers", tags=["attempts"])


def _to_session_read(
    attempt: ExamAttempt, paper: QuestionPaper, questions: list[Question]
) -> ExamSessionRead:
    base = ExamAttemptRead.model_validate(attempt).model_dump()
    exam_questions = [
        ExamQuestionPublic(
            id=q.id,
            question_number=q.question_number,
            question_type=q.question_type,
            prompt_text=q.prompt_text,
            has_prompt_image=q.prompt_image is not None,
            points=q.points,
            options=[
                ExamQuestionOptionPublic(
                    id=o.id,
                    option_label=o.option_label,
                    option_text=o.option_text,
                    has_image=o.option_image is not None,
                    display_order=o.display_order,
                )
                for o in sorted(q.options, key=lambda o: o.display_order)
            ],
        )
        for q in sorted(questions, key=lambda q: q.question_number)
    ]
    return ExamSessionRead(**base, paper_title=paper.title, questions=exam_questions)


@paper_router.post(
    "/{paper_id}/attempts",
    response_model=ExamSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def start_attempt(
    paper_id: uuid.UUID, payload: ExamAttemptStart, db: Session = Depends(get_db)
) -> ExamSessionRead:
    paper = papers_crud.get_paper_by_id(db, paper_id)
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question paper not found."
        )
    if paper.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This paper isn't published yet.",
        )

    questions = questions_crud.list_questions_for_paper(db, paper_id)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This paper has no questions yet.",
        )

    display_name = payload.student_name.strip()
    if not display_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Student name is required."
        )
    student = students_crud.get_student_by_name(db, display_name)
    if student is None:
        student = students_crud.create_student(db, display_name=display_name)

    attempt = attempts_crud.create_attempt(
        db, paper=paper, student=student, questions=questions
    )
    return _to_session_read(attempt, paper, questions)


@paper_router.get("/{paper_id}/attempts", response_model=list[ExamAttemptRead])
def list_paper_attempts(
    paper_id: uuid.UUID,
    student_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
) -> list[ExamAttemptRead]:
    return list(attempts_crud.list_attempts_for_paper(db, paper_id, student_id))


@router.get("/{attempt_id}", response_model=ExamSessionRead)
def get_attempt_session(
    attempt_id: uuid.UUID, db: Session = Depends(get_db)
) -> ExamSessionRead:
    attempt = attempts_crud.get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found."
        )
    paper = papers_crud.get_paper_by_id(db, attempt.paper_id)
    questions = questions_crud.list_questions_for_paper(db, attempt.paper_id)
    return _to_session_read(attempt, paper, questions)


@router.post("/{attempt_id}/submit", response_model=AttemptReviewRead)
def submit_attempt(
    attempt_id: uuid.UUID, payload: AttemptSubmit, db: Session = Depends(get_db)
) -> AttemptReviewRead:
    attempt = attempts_crud.get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found."
        )
    if attempt.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This attempt has already been submitted.",
        )

    paper = papers_crud.get_paper_by_id(db, attempt.paper_id)
    questions = questions_crud.list_questions_for_paper(db, attempt.paper_id)

    attempt = attempts_crud.submit_attempt(
        db,
        attempt=attempt,
        questions=questions,
        answers=[a.model_dump() for a in payload.answers],
        reason=payload.reason,
    )
    answer_rows = attempts_crud.get_attempt_answers_with_details(db, attempt.id)
    return _build_review(attempt, paper, questions, answer_rows)


@router.get("/{attempt_id}/review", response_model=AttemptReviewRead)
def review_attempt(
    attempt_id: uuid.UUID, db: Session = Depends(get_db)
) -> AttemptReviewRead:
    attempt = attempts_crud.get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found."
        )
    if attempt.status == "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This attempt hasn't been submitted yet.",
        )

    paper = papers_crud.get_paper_by_id(db, attempt.paper_id)
    questions = questions_crud.list_questions_for_paper(db, attempt.paper_id)
    answer_rows = attempts_crud.get_attempt_answers_with_details(db, attempt.id)
    return _build_review(attempt, paper, questions, answer_rows)


def _build_review(
    attempt: ExamAttempt,
    paper: QuestionPaper,
    questions: list[Question],
    answer_rows: list[AttemptAnswer],
) -> AttemptReviewRead:
    answers_by_question_id = {row.question_id: row for row in answer_rows}

    reviews = []
    for question in sorted(questions, key=lambda q: q.question_number):
        row = answers_by_question_id.get(question.id)
        options = [
            QuestionOptionRead(
                id=o.id,
                question_id=o.question_id,
                option_label=o.option_label,
                option_text=o.option_text,
                has_image=o.option_image is not None,
                is_correct=o.is_correct,
                display_order=o.display_order,
            )
            for o in sorted(question.options, key=lambda o: o.display_order)
        ]
        is_correct = row.is_correct if row else (None if question.question_type == "short_answer" else False)
        reviews.append(
            AnswerReviewRead(
                question_id=question.id,
                question_number=question.question_number,
                question_type=question.question_type,
                prompt_text=question.prompt_text,
                explanation_text=question.explanation_text,
                points=question.points,
                options=options,
                selected_option_id=row.selected_option_id if row else None,
                short_answer_text=row.short_answer_text if row else None,
                short_answer_expected=question.short_answer_expected,
                is_correct=is_correct,
            )
        )

    base = ExamAttemptRead.model_validate(attempt).model_dump()
    return AttemptReviewRead(**base, paper_title=paper.title, answers=reviews)
