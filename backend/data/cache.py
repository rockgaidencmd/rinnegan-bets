"""HTTP response cache backed by SQLite (data_cache table).

Provides read-through cache pattern with TTL. Atomic UPSERT prevents
race conditions when multiple requests hit the same key simultaneously.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from db.models import DataCache


DEFAULT_TTL = timedelta(hours=24)


class CacheService:
    """Read-through cache with TTL. Survives process restarts."""

    def __init__(self, session: Session, default_ttl: timedelta = DEFAULT_TTL):
        self._session = session
        self._default_ttl = default_ttl

    def get(self, key: str) -> dict | None:
        """Return cached value if present AND not expired. None otherwise.

        Does not delete expired entries (sweep() handles that).
        """
        now = datetime.now(timezone.utc)
        row = self._session.execute(
            select(DataCache).where(
                DataCache.key == key,
                DataCache.expires_at > now,
            )
        ).scalar_one_or_none()
        return row.payload if row else None

    def set(self, key: str, payload: dict, ttl: timedelta | None = None) -> None:
        """Atomic UPSERT (INSERT or UPDATE if key exists).

        SQLite-specific: uses ON CONFLICT clause. If we ever switch DBs,
        only this method needs updating.
        """
        now = datetime.now(timezone.utc)
        expires_at = now + (ttl or self._default_ttl)

        stmt = sqlite_insert(DataCache).values(
            key=key,
            payload=payload,
            fetched_at=now,
            expires_at=expires_at,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["key"],
            set_={
                "payload": stmt.excluded.payload,
                "fetched_at": stmt.excluded.fetched_at,
                "expires_at": stmt.excluded.expires_at,
            },
        )
        self._session.execute(stmt)
        self._session.commit()

    def invalidate(self, key: str) -> bool:
        """Delete a specific cache entry. Returns True if entry existed."""
        result = self._session.execute(
            delete(DataCache).where(DataCache.key == key)
        )
        self._session.commit()
        return result.rowcount > 0

    def sweep(self) -> int:
        """Delete all expired entries. Returns count deleted.

        Run periodically (startup, daily cron) to keep cache table small.
        """
        now = datetime.now(timezone.utc)
        result = self._session.execute(
            delete(DataCache).where(DataCache.expires_at <= now)
        )
        self._session.commit()
        return result.rowcount


def make_cache_key(*parts: Any) -> str:
    """Build a deterministic cache key from parts.

    Example: make_cache_key("fd", "matches", "PL", "2025-05-19")
             → "fd:matches:PL:2025-05-19"
    """
    return ":".join(str(p) for p in parts)
