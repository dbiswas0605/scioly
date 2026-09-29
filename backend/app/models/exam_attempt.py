"""ExamAttempt model — one attempt by a student at a question paper."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="in_progress"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_minutes_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    max_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    correct_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_questions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    student: Mapped["Student"] = relationship("Student", back_populates="attempts")
    paper: Mapped["QuestionPaper"] = relationship(
        "QuestionPaper", back_populates="attempts"
    )
    answers: Mapped[list["AttemptAnswer"]] = relationship(
        "AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress','submitted','timed_out','abandoned')",
            name="status_valid",
        ),
        UniqueConstraint(
            "student_id",
            "paper_id",
            "attempt_number",
            name="uq_exam_attempts_student_paper_attempt_number",
        ),
        Index("ix_exam_attempts_student_id", "student_id"),
        Index("ix_exam_attempts_paper_id", "paper_id"),
        Index("ix_exam_attempts_student_id_paper_id", "student_id", "paper_id"),
    )
