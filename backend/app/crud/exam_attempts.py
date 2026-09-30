"""CRUD helpers for taking and scoring ExamAttempts.

Scoring policy: only `mcq` answers are auto-graded (is_correct = whether the
selected option's is_correct flag is set); `short_answer` answers are
stored with is_correct left null (ungraded) and don't count toward
max_score/correct_count.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.attempt_answer import AttemptAnswer
from app.models.exam_attempt import ExamAttempt
from app.models.question import Question
from app.models.question_paper import QuestionPaper
from app.models.student import Student


def list_attempts(db: Session) -> list[ExamAttempt]:
    return list(db.scalars(select(ExamAttempt).order_by(ExamAttempt.created_at.desc())))


def get_attempt(db: Session, attempt_id: uuid.UUID) -> ExamAttempt | None:
    return db.get(ExamAttempt, attempt_id)


def list_attempts_for_paper(
    db: Session, paper_id: uuid.UUID, student_id: uuid.UUID | None = None
) -> list[ExamAttempt]:
    stmt = select(ExamAttempt).where(ExamAttempt.paper_id == paper_id)
    if student_id is not None:
        stmt = stmt.where(ExamAttempt.student_id == student_id)
    stmt = stmt.order_by(ExamAttempt.attempt_number)
    return list(db.scalars(stmt))


def list_attempts_for_student(db: Session, student_id: uuid.UUID) -> list[ExamAttempt]:
    """All of one student's attempts across every paper — used to decorate
    the Practice subject/paper tiles with "already taken" + score."""
    return list(
        db.scalars(
            select(ExamAttempt)
            .where(ExamAttempt.student_id == student_id)
            .order_by(ExamAttempt.paper_id, ExamAttempt.attempt_number)
        )
    )


def create_attempt(
    db: Session,
    *,
    paper: QuestionPaper,
    student: Student,
    questions: list[Question],
) -> ExamAttempt:
    next_attempt_number = (
        db.scalar(
            select(func.coalesce(func.max(ExamAttempt.attempt_number), 0)).where(
                ExamAttempt.paper_id == paper.id, ExamAttempt.student_id == student.id
            )
        )
        or 0
    ) + 1

    max_score = sum(
        (q.points for q in questions if q.question_type == "mcq"), start=0
    )

    attempt = ExamAttempt(
        student_id=student.id,
        paper_id=paper.id,
        attempt_number=next_attempt_number,
        status="in_progress",
        duration_minutes_snapshot=paper.default_duration_minutes,
        max_score=max_score,
        total_questions=len(questions),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def get_attempt_answers_with_details(
    db: Session, attempt_id: uuid.UUID
) -> list[AttemptAnswer]:
    return list(
        db.scalars(
            select(AttemptAnswer)
            .where(AttemptAnswer.attempt_id == attempt_id)
            .options(
                joinedload(AttemptAnswer.question).joinedload(Question.options)
            )
        ).unique()
    )


def submit_attempt(
    db: Session,
    *,
    attempt: ExamAttempt,
    questions: list[Question],
    answers: list[dict[str, Any]],
    reason: str,
) -> ExamAttempt:
    questions_by_id = {q.id: q for q in questions}
    options_by_id = {
        option.id: option for q in questions for option in q.options
    }

    # Replace any prior answers for this attempt (re-submitting overwrites,
    # though the frontend only calls this once per attempt in practice).
    for existing in list(attempt.answers):
        db.delete(existing)
    db.flush()

    correct_count = 0
    score = 0

    for answer in answers:
        question = questions_by_id.get(answer["question_id"])
        if question is None:
            continue  # ignore answers for questions not on this paper

        is_correct: bool | None = None
        selected_option_id = answer.get("selected_option_id")
        if question.question_type == "mcq":
            selected_option = (
                options_by_id.get(selected_option_id) if selected_option_id else None
            )
            is_correct = bool(selected_option and selected_option.is_correct)
            if is_correct:
                correct_count += 1
                score += question.points

        db.add(
            AttemptAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option_id=selected_option_id
                if question.question_type == "mcq"
                else None,
                short_answer_text=answer.get("short_answer_text")
                if question.question_type == "short_answer"
                else None,
                is_correct=is_correct,
                answered_at=func.now(),
            )
        )

    attempt.status = reason
    attempt.submitted_at = func.now()
    attempt.score = score
    attempt.correct_count = correct_count

    db.commit()
    db.refresh(attempt)
    return attempt
