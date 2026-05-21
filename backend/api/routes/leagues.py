"""League catalog + match listing endpoints."""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import and_, func, or_, select

from api.deps import DbSession
from api.schemas.leagues import (
    LeagueListResponse,
    LeagueSummary,
    MatchListResponse,
    MatchSummary,
)
from api.schemas.teams import TeamResponse
from core.leagues import LEAGUES
from db.models import Match, Team


router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/leagues", response_model=LeagueListResponse)
def list_leagues(db: DbSession) -> LeagueListResponse:
    """All supported leagues from core/leagues.py with current team + match counts.

    Returns every league the app supports — even ones with 0 teams/matches.
    The frontend uses this as the canonical league catalog (no hardcoding).
    """
    team_counts = dict(db.execute(
        select(Team.league, func.count(Team.id)).group_by(Team.league)
    ).all())
    match_counts = dict(db.execute(
        select(Match.league, func.count(Match.id)).group_by(Match.league)
    ).all())

    leagues = [
        LeagueSummary(
            code=info.code,
            name=info.name,
            country=info.country,
            team_count=team_counts.get(info.code, 0),
            match_count=match_counts.get(info.code, 0),
        )
        for info in sorted(LEAGUES.values(), key=lambda i: i.name)
    ]
    return LeagueListResponse(leagues=leagues, total=len(leagues))


@router.get("/leagues/{league_code}/teams", response_model=list[TeamResponse])
def list_teams_by_league(league_code: str, db: DbSession) -> list[TeamResponse]:
    """All teams in a league, alphabetically."""
    teams = db.execute(
        select(Team).where(Team.league == league_code).order_by(Team.name)
    ).scalars().all()
    if not teams:
        raise HTTPException(404, f"No teams found for league '{league_code}'")
    return [TeamResponse.model_validate(t) for t in teams]


@router.get("/matches", response_model=MatchListResponse)
def list_matches(
    db: DbSession,
    league: str | None = Query(None, description="Filter by league code"),
    team_id: int | None = Query(None, description="Filter by team participation"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, description="Skip this many rows (pagination)"),
) -> MatchListResponse:
    """List recent finished matches with offset/limit pagination.

    Returns both `total` (rows in this page) and `total_available` (the
    full count matching the filter), so the frontend can show "X of Y"
    and know when to disable the "Cargar más" button.
    """
    conditions = [Match.home_goals.is_not(None)]
    if league:
        conditions.append(Match.league == league)
    if team_id:
        conditions.append(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id)
        )
    where_clause = and_(*conditions)

    total_available = db.execute(
        select(func.count()).select_from(Match).where(where_clause)
    ).scalar_one()

    matches = db.execute(
        select(Match)
        .where(where_clause)
        .order_by(Match.match_date.desc(), Match.id.desc())
        .offset(offset)
        .limit(limit)
    ).scalars().all()

    # Pre-fetch team names in one query
    team_ids = {m.home_team_id for m in matches} | {m.away_team_id for m in matches}
    teams_by_id = {
        t.id: t.name for t in db.execute(
            select(Team).where(Team.id.in_(team_ids))
        ).scalars().all()
    }

    results = [
        MatchSummary(
            id=m.id,
            league=m.league,
            match_date=m.match_date,
            home_team_id=m.home_team_id,
            home_team_name=teams_by_id.get(m.home_team_id, "?"),
            away_team_id=m.away_team_id,
            away_team_name=teams_by_id.get(m.away_team_id, "?"),
            home_goals=m.home_goals,
            away_goals=m.away_goals,
            result=m.result,
            home_xg=m.home_xg,
            away_xg=m.away_xg,
        )
        for m in matches
    ]
    return MatchListResponse(
        matches=results,
        total=len(results),
        total_available=total_available,
        offset=offset,
    )
