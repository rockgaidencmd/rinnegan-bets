"""League + match listing schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# League names for display (internal codes → human-readable)
LEAGUE_DISPLAY = {
    "PL": "Premier League",
    "PD": "La Liga",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    "FL1": "Ligue 1",
    "CL": "Champions League",
    "LIB": "Copa Libertadores",
    "EC1": "LigaPro Ecuador",
}


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
