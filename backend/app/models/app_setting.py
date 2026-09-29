"""AppSetting model — generic key/value application settings, DB-driven."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="string"
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "value_type IN ('string','integer','boolean','json')",
            name="value_type_valid",
        ),
    )
