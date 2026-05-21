"""Admin endpoints — manual operations the UI can trigger.

NOT exposed publicly in a real product; here it's fine because the app
runs locally / on the user's own machine.
"""

import logging
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from api.deps import DbSession
from core.leagues import LEAGUES
from db.models import Match, Team


logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

router = APIRouter(prefix="/api/admin", tags=["admin"])


class RefreshRequest(BaseModel):
    """Empty body for now; reserved for future filters (per-league refresh, etc.)."""


class RefreshResponse(BaseModel):
    status: str           # 'started' | 'failed'
    message: str
    teams_before: int
    matches_before: int


class DataStatsResponse(BaseModel):
    teams: int
    matches: int
    matches_with_xg: int
    leagues_with_data: int


@router.get("/stats", response_model=DataStatsResponse)
def get_data_stats(db: DbSession) -> DataStatsResponse:
    """Snapshot of what's in the DB right now."""
    teams = db.query(Team).count()
    matches = db.query(Match).count()
    with_xg = db.query(Match).filter(Match.home_xg.is_not(None)).count()
    distinct_leagues = db.query(Match.league).distinct().count()
    return DataStatsResponse(
        teams=teams,
        matches=matches,
        matches_with_xg=with_xg,
        leagues_with_data=distinct_leagues,
    )


@router.post("/refresh", response_model=RefreshResponse, status_code=202)
def refresh_data(
    _: RefreshRequest, background_tasks: BackgroundTasks, db: DbSession,
) -> RefreshResponse:
    """Kick off a re-seed of matches. Returns immediately (202 Accepted),
    work happens in the background. Frontend can poll /api/admin/stats
    to see when counts change.

    Why background: full seed takes 5-10 min — would time out an HTTP request.
    """
    teams_before = db.query(Team).count()
    matches_before = db.query(Match).count()

    background_tasks.add_task(_run_seed_matches)

    return RefreshResponse(
        status="started",
        message=(
            "Seed started in background. Takes ~5-10 min. "
            "Poll /api/admin/stats to watch match count grow."
        ),
        teams_before=teams_before,
        matches_before=matches_before,
    )


def _run_seed_matches() -> None:
    """Run the unified seed script (--all leagues) as a subprocess so its
    DB session is independent of the HTTP request's session (which closes
    when the response is sent).
    """
    script = BACKEND_DIR / "scripts" / "seed_matches.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--all"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
            timeout=30 * 60,  # 30 min ceiling — full re-seed of every league
        )
        if result.returncode != 0:
            logger.error("Seed failed (exit %s): %s", result.returncode, result.stderr[-500:])
        else:
            logger.info("Seed finished successfully")
    except subprocess.TimeoutExpired:
        logger.error("Seed timed out after 30 minutes")
    except Exception as e:
        logger.exception("Seed subprocess crashed: %s", e)
