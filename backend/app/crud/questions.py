"""CRUD helpers for the Question / QuestionOption resources."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, joinedload

from app.models.question import Question
from app.models.question_option import QuestionOption


def list_questions_for_paper(db: Session, paper_id: uuid.UUID) -> list[Question]:
    return list(
        db.scalars(
            select(Question)
            .where(Question.paper_id == paper_id)
            .options(joinedload(Question.options))
            .order_by(Question.question_number)
        ).unique()
    )


def get_question_for_paper(
    db: Session, paper_id: uuid.UUID, question_id: uuid.UUID
) -> Question | None:
    return db.scalar(
        select(Question)
        .where(Question.paper_id == paper_id, Question.id == question_id)
        .options(joinedload(Question.options))
    )


def count_unreviewed_questions(db: Session, paper_id: uuid.UUID) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Question)
            .where(Question.paper_id == paper_id, Question.is_reviewed.is_(False))
        )
        or 0
    )


def list_mcq_question_numbers_missing_correct_answer(
    db: Session, paper_id: uuid.UUID
) -> list[int]:
    """Defense-in-depth for `publish_paper` — normally
    `update_question`/the PATCH endpoint already rejects saving an mcq
    question with no correct option marked, but this catches anything that
    slipped through (e.g. bad data from an earlier bug)."""
    questions = list_questions_for_paper(db, paper_id)
    return [
        q.question_number
        for q in questions
        if q.question_type == "mcq"
        and sum(1 for o in q.options if o.is_correct) != 1
    ]


def confirm_all_questions(db: Session, paper_id: uuid.UUID) -> None:
    """Bulk-accept every question's current server-side state (prompt,
    options, correct answer) as reviewed — the "Save & Confirm All" action
    on the upload review screen. Callers must check
    `list_mcq_question_numbers_missing_correct_answer` first; this doesn't
    re-validate, it just flips the flag."""
    db.execute(
        update(Question).where(Question.paper_id == paper_id).values(is_reviewed=True)
    )
    db.commit()


def replace_questions_for_paper(
    db: Session, paper_id: uuid.UUID, parsed_questions: list[dict[str, Any]]
) -> list[Question]:
    """Delete any existing questions for this paper and insert the freshly
    parsed ones (each starting out unreviewed, pending parent confirmation).
    """
    db.execute(delete(Question).where(Question.paper_id == paper_id))
    db.flush()

    questions: list[Question] = []
    for parsed in parsed_questions:
        question = Question(
            paper_id=paper_id,
            question_number=parsed["question_number"],
            question_type=parsed["question_type"],
            prompt_text=parsed["prompt_text"],
            explanation_text=parsed.get("explanation_text"),
            short_answer_expected=parsed.get("short_answer_expected"),
            llm_suggested_answer=parsed.get("llm_suggested_answer"),
            is_reviewed=False,
        )
        question.options = [
            QuestionOption(
                option_label=option["option_label"],
                option_text=option.get("option_text"),
                is_correct=bool(option.get("is_correct")),
                display_order=option.get("display_order", index),
            )
            for index, option in enumerate(parsed.get("options") or [])
        ]
        db.add(question)
        questions.append(question)

    db.commit()
    for question in questions:
        db.refresh(question)
    return questions


def update_question(
    db: Session, question: Question, data: dict[str, Any]
) -> Question:
    """Update a question's fields and fully replace its options list.
    Always marks the question reviewed — this is called when a parent saves
    their edits/confirmation on the review screen.
    """
    for field in (
        "question_type",
        "prompt_text",
        "explanation_text",
        "short_answer_expected",
        "points",
    ):
        if field in data:
            setattr(question, field, data[field])

    if "options" in data:
        # Delete the old rows explicitly (and flush) before inserting the
        # new ones, rather than reassigning `question.options` and relying
        # on the ORM's delete-orphan cascade — the new options reuse the
        # same option_label values ('A', 'B', ...), and the cascade doesn't
        # guarantee deleting the old rows before inserting the new ones,
        # which trips the (question_id, option_label) unique constraint.
        db.execute(delete(QuestionOption).where(QuestionOption.question_id == question.id))
        db.flush()
        for index, option in enumerate(data["options"]):
            db.add(
                QuestionOption(
                    question_id=question.id,
                    option_label=option["option_label"],
                    option_text=option.get("option_text"),
                    is_correct=bool(option.get("is_correct")),
                    display_order=option.get("display_order", index),
                )
            )

    question.is_reviewed = True

    # `question` is already persistent (loaded in this session) so its
    # scalar attribute changes are tracked automatically. Deliberately not
    # calling db.add(question) here — that would cascade into the (now
    # stale, already-deleted) in-memory `options` collection and raise
    # "Instance has been deleted."
    db.commit()
    db.refresh(question, attribute_names=["options"])
    return question
