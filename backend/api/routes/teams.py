"""Team endpoints — search/autocomplete + recent stats."""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select

from api.deps import DbSession
from api.schemas.teams import TeamResponse, TeamSearchResponse, TeamStatsResponse
from core.features.extractor import extract_team_features
from data.team_search import find_teams_by_name
from db.models import Match, Team


router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("/search", response_model=TeamSearchResponse)
def search_teams(
    db: DbSession,
    q: str = Query(min_length=1, description="Team name or alias"),
    limit: int = Query(10, ge=1, le=50),
) -> TeamSearchResponse:
    """Find teams matching a query string. Used for autocomplete on the frontend.

    Resolves common aliases (IDV, ManU, BSC, etc.) before doing the DB lookup.
    """
    teams = find_teams_by_name(db, q)[:limit]
    return TeamSearchResponse(
        query=q,
        results=[TeamResponse.model_validate(t) for t in teams],
        count=len(teams),
    )


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(team_id: int, db: DbSession) -> TeamResponse:
    """Get a single team by id."""
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    return TeamResponse.model_validate(team)


@router.get("/{team_id}/stats", response_model=TeamStatsResponse)
def get_team_stats(
    team_id: int, db: DbSession, last: int = Query(10, ge=1, le=20),
) -> TeamStatsResponse:
    """Aggregated stats over the team's last N finished matches."""
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

    matches = db.execute(
        select(Match)
        .where(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))
        .where(Match.home_goals.is_not(None))
        .order_by(Match.match_date.desc())
        .limit(last)
    ).scalars().all()

    features = extract_team_features(matches, team_id)
    return TeamStatsResponse(
        team_id=team_id,
        team_name=team.name,
        matches_analyzed=features.matches_analyzed,
        wins=features.wins,
        draws=features.draws,
        losses=features.losses,
        form_score=features.form_score,
        avg_goals_for=features.avg_goals_for,
        avg_goals_against=features.avg_goals_against,
        avg_xg_for=features.avg_xg_for,
        avg_xg_against=features.avg_xg_against,
        avg_possession=features.avg_possession,
        avg_shots_on_target=features.avg_shots_on_target,
        avg_corners=features.avg_corners,
    )
