"""Question model — a single MCQ or short-answer question within a paper."""
from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    prompt_image_content_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_answer_expected: Mapped[str | None] = mapped_column(Text, nullable=True)
    points: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="1.0"
    )
    llm_suggested_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_reviewed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    paper: Mapped["QuestionPaper"] = relationship(
        "QuestionPaper", back_populates="questions"
    )
    options: Mapped[list["QuestionOption"]] = relationship(
        "QuestionOption", back_populates="question", cascade="all, delete-orphan"
    )
    attempt_answers: Mapped[list["AttemptAnswer"]] = relationship(
        "AttemptAnswer", back_populates="question", passive_deletes=True
    )

    __table_args__ = (
        CheckConstraint(
            "question_type IN ('mcq','short_answer')", name="question_type_valid"
        ),
        UniqueConstraint("paper_id", "question_number", name="uq_questions_paper_question_number"),
        Index("ix_questions_paper_id", "paper_id"),
    )
