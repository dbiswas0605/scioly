"""QuestionPaper model — an uploaded/parsed exam paper for a subject."""
from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class QuestionPaper(Base, TimestampMixin):
    __tablename__ = "question_papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_file: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    source_file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )
    default_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="30"
    )
    total_questions: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="papers")
    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="paper", cascade="all, delete-orphan"
    )
    attempts: Mapped[list["ExamAttempt"]] = relationship(
        "ExamAttempt", back_populates="paper", passive_deletes=True
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','pending_review','published','archived')",
            name="status_valid",
        ),
        Index("ix_question_papers_subject_id", "subject_id"),
        Index("ix_question_papers_status", "status"),
    )
