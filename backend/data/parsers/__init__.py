"""Parsers convert raw API responses to normalized internal types."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ParsedTeam:
    """Normalized team data — same shape regardless of source API."""

    name: str
    slug: str
    league: str  # internal league code (PL, PD, EC1, etc.)
    country: str | None = None
    football_data_id: int | None = None
    sofascore_id: int | None = None


@dataclass(frozen=True)
class ParsedMatch:
    """Normalized match data with optional statistics.

    Stats fields are None until statistics endpoint is fetched separately
    and merged via merge_statistics().
    """

    external_id: str          # source-specific unique ID (e.g., SofaScore event id)
    source: str               # 'sofascore' or 'football_data'
    league: str               # internal league code
    home_team_sofascore_id: int
    away_team_sofascore_id: int
    home_team_name: str       # for matching to teams table
    away_team_name: str
    match_date: datetime
    status: str               # 'finished', 'live', 'scheduled'

    home_goals: int | None = None
    away_goals: int | None = None
    result: str | None = None  # 'H' | 'D' | 'A'

    # Stats — populated by merge_statistics()
    home_xg: float | None = None
    away_xg: float | None = None
    home_possession: float | None = None
    away_possession: float | None = None
    home_shots_on_target: int | None = None
    away_shots_on_target: int | None = None
    home_corners: int | None = None
    away_corners: int | None = None
    home_yellow_cards: int | None = None
    away_yellow_cards: int | None = None
