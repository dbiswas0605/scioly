"""QuestionOption model — one selectable answer choice for an MCQ question."""
from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_label: Mapped[str] = mapped_column(String(10), nullable=False)
    option_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    option_image_content_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    is_correct: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    question: Mapped["Question"] = relationship("Question", back_populates="options")
    selected_in_answers: Mapped[list["AttemptAnswer"]] = relationship(
        "AttemptAnswer", back_populates="selected_option"
    )

    __table_args__ = (
        UniqueConstraint(
            "question_id", "option_label", name="uq_question_options_question_option_label"
        ),
        Index("ix_question_options_question_id", "question_id"),
    )
