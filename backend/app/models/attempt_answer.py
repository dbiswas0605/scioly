"""AttemptAnswer model — a student's recorded answer to one question in an attempt."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

attempt_answer_options = Table(
    "attempt_answer_options",
    Base.metadata,
    Column(
        "attempt_answer_id",
        UUID(as_uuid=True),
        ForeignKey("attempt_answers.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "option_id",
        UUID(as_uuid=True),
        ForeignKey("question_options.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("ix_attempt_answer_options_option_id", "option_id"),
)


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exam_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    selected_option_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_options.id", ondelete="SET NULL"),
        nullable=True,
    )
    short_answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    attempt: Mapped["ExamAttempt"] = relationship(
        "ExamAttempt", back_populates="answers"
    )
    question: Mapped["Question"] = relationship(
        "Question", back_populates="attempt_answers"
    )
    selected_option: Mapped["QuestionOption | None"] = relationship(
        "QuestionOption", back_populates="selected_in_answers"
    )
    selected_options: Mapped[list["QuestionOption"]] = relationship(
        "QuestionOption", secondary=attempt_answer_options
    )

    __table_args__ = (
        UniqueConstraint(
            "attempt_id", "question_id", name="uq_attempt_answers_attempt_question"
        ),
        Index("ix_attempt_answers_attempt_id", "attempt_id"),
        Index("ix_attempt_answers_question_id", "question_id"),
    )
