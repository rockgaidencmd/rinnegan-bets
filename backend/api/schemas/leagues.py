"""League + match listing schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core.leagues import LEAGUES


# Display name lookup — derived from the single source of truth.
LEAGUE_DISPLAY = {code: info.name for code, info in LEAGUES.items()}


class LeagueSummary(BaseModel):
    code: str
    name: str
    country: str | None = None
    team_count: int
    match_count: int


class LeagueListResponse(BaseModel):
    leagues: list[LeagueSummary]
    total: int


class MatchSummary(BaseModel):
    """A match row condensed for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    league: str
    match_date: datetime
    home_team_id: int
    home_team_name: str
    away_team_id: int
    away_team_name: str
    home_goals: int | None = None
    away_goals: int | None = None
    result: str | None = None
    home_xg: float | None = None
    away_xg: float | None = None


class MatchListResponse(BaseModel):
    matches: list[MatchSummary]
    total: int
