"""Shared Pydantic types for API responses.

The big one: UtcDatetime. SQLite doesn't preserve timezone info, so a
column we stored with tz=UTC comes back as a NAIVE datetime when read
via SQLAlchemy. If we let Pydantic serialize that as-is, the JSON
string has no 'Z' suffix and the frontend's `new Date(...)` parses it
as LOCAL time — which broke our match dates by 1 day for late-night
games (e.g. 2026-05-19T00:00:00 was actually 18-may 19:00 in Ecuador).

UtcDatetime normalizes any datetime to tz-aware UTC at the model
boundary, so serialized output always includes the timezone offset.
"""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BeforeValidator


def _ensure_utc(value):
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


UtcDatetime = Annotated[datetime, BeforeValidator(_ensure_utc)]
