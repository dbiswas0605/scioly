"""Student model — a tutoring student who takes practice exams."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    attempts: Mapped[list["ExamAttempt"]] = relationship(
        "ExamAttempt", back_populates="student"
    )

    __table_args__ = (
        Index("ix_students_lower_display_name", func.lower(display_name), unique=True),
    )
