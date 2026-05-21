"""Upcoming match fixtures — powers the "pick a real upcoming match" UI."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from api.deps import BankrollDep, DbSession  # noqa: F401 (BankrollDep unused here)
from api.schemas.fixtures import FixtureListResponse, FixtureSummary
from core.leagues import LEAGUES
from data.cache import CacheService
from data.fetchers.base import FetchError
from data.fetchers.sofascore import SofaScoreFetcher
from data.parsers.sofascore_match_parser import parse_upcoming_fixtures
from db.models import Team


router = APIRouter(prefix="/api", tags=["fixtures"])


@router.get("/fixtures", response_model=FixtureListResponse)
def list_fixtures(
    db: DbSession,
    league: str = Query(..., description="League code (e.g. PL, EC1)"),
    days: int = Query(7, ge=1, le=30, description="Only fixtures within N days"),
    limit: int = Query(20, ge=1, le=50),
) -> FixtureListResponse:
    """Upcoming fixtures in the next N days for a league.

    Hits SofaScore via the cached fetcher; results refresh every 30 min.
    Maps each team to its internal id when available (so the frontend
    can call /api/predictions without an extra lookup).
    """
    info = LEAGUES.get(league)
    if info is None:
        raise HTTPException(404, f"Unknown league '{league}'")

    cache = CacheService(db)
    fetcher = SofaScoreFetcher(cache)

    season_id = _latest_season(fetcher, info.sofascore_id)
    if season_id is None:
        return FixtureListResponse(league=league, fixtures=[], total=0)

    try:
        payload = fetcher.get_tournament_upcoming(info.sofascore_id, season_id)
    except FetchError as e:
        raise HTTPException(502, f"Upstream fetch failed: {e}")

    fixtures = parse_upcoming_fixtures(payload)
    cutoff = datetime.now(timezone.utc) + timedelta(days=days)
    fixtures = [f for f in fixtures if f.match_date <= cutoff][:limit]

    sofa_ids = {f.home_team_sofascore_id for f in fixtures} | {
        f.away_team_sofascore_id for f in fixtures
    }
    teams_by_sofa = _teams_by_sofascore_id(db, sofa_ids)

    summaries = [
        FixtureSummary(
            league=f.league,
            match_date=f.match_date,
            home_team_id=teams_by_sofa.get(f.home_team_sofascore_id),
            home_team_name=f.home_team_name,
            away_team_id=teams_by_sofa.get(f.away_team_sofascore_id),
            away_team_name=f.away_team_name,
        )
        for f in fixtures
    ]
    return FixtureListResponse(league=league, fixtures=summaries, total=len(summaries))


def _latest_season(fetcher: SofaScoreFetcher, tournament_id: int) -> int | None:
    seasons = fetcher.get_tournament_seasons(tournament_id).get("seasons", [])
    return seasons[0]["id"] if seasons else None


def _teams_by_sofascore_id(db, sofa_ids: set[int]) -> dict[int, int]:
    """Map sofascore_id → internal team.id (preferring most-recent row if duplicated)."""
    if not sofa_ids:
        return {}
    teams = db.execute(
        select(Team).where(Team.sofascore_id.in_(sofa_ids))
    ).scalars().all()
    mapping: dict[int, int] = {}
    for t in teams:
        # If a team appears in multiple leagues, first one wins (good enough for picker)
        mapping.setdefault(t.sofascore_id, t.id)
    return mapping
