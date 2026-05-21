"""Schema for upcoming match listings."""

from datetime import datetime

from pydantic import BaseModel


class FixtureSummary(BaseModel):
    """A scheduled match that hasn't been played yet.

    No goals, xG, or stats — those exist only post-match.
    home_team_id / away_team_id are nullable because the fixture might
    involve a team we haven't seeded yet (rare).
    """

    league: str
    match_date: datetime
    home_team_id: int | None = None
    home_team_name: str
    away_team_id: int | None = None
    away_team_name: str


class FixtureListResponse(BaseModel):
    league: str
    fixtures: list[FixtureSummary]
    total: int
