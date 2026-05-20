"""Reusable mixins for ORM models."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Adds created_at and updated_at columns.

    created_at: set by DB on INSERT (server_default)
    updated_at: set by ORM on UPDATE (SQLite has no ON UPDATE CURRENT_TIMESTAMP)
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
