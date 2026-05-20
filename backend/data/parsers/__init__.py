"""Parsers convert raw API responses to normalized internal types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedTeam:
    """Normalized team data — same shape regardless of source API."""

    name: str
    slug: str
    league: str  # internal league code (PL, PD, EC1, etc.)
    country: str | None = None
    football_data_id: int | None = None
    sofascore_id: int | None = None
