"""Subject model — top-level categorization for question papers."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    papers: Mapped[list["QuestionPaper"]] = relationship(
        "QuestionPaper", back_populates="subject"
    )

    __table_args__ = (
        Index("ix_subjects_lower_name", func.lower(name), unique=True),
    )
