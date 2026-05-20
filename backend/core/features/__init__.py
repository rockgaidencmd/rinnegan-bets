"""Feature extractors — pure functions over match data.

Input: list of objects matching MatchData protocol (typically ORM Match rows).
Output: TeamFeatures (frozen dataclass from core.types).

Core never imports from db/. Tests use SimpleNamespace or mock objects
that satisfy MatchData structurally.
"""

from typing import Protocol


class MatchData(Protocol):
    """Structural type — anything with these attributes counts as MatchData."""

    home_team_id: int
    away_team_id: int
    home_goals: int | None
    away_goals: int | None
    home_xg: float | None
    away_xg: float | None
    home_possession: float | None
    away_possession: float | None
    home_shots_on_target: int | None
    away_shots_on_target: int | None
    home_corners: int | None
    away_corners: int | None
