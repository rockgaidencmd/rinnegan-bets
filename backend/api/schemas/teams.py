"""Team schemas — DTOs separated from ORM models."""

from pydantic import BaseModel, ConfigDict


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    league: str
    country: str | None = None
    football_data_id: int | None = None
    sofascore_id: int | None = None


class TeamSearchResponse(BaseModel):
    """Result of an autocomplete query."""

    query: str
    results: list[TeamResponse]
    count: int


class TeamStatsResponse(BaseModel):
    """Recent stats for a team based on its last N matches."""

    team_id: int
    team_name: str
    matches_analyzed: int
    wins: int
    draws: int
    losses: int
    form_score: float
    avg_goals_for: float
    avg_goals_against: float
    avg_xg_for: float | None = None
    avg_xg_against: float | None = None
    avg_possession: float | None = None
    avg_shots_on_target: float | None = None
    avg_corners: float | None = None
