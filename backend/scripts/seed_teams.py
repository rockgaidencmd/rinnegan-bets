#!/usr/bin/env python3
"""Seed the teams table with real data from Football-Data + SofaScore.

Run once after initial DB migration. Idempotent — safe to re-run
(uses INSERT OR IGNORE on (slug, league)).

Usage:
    python scripts/seed_teams.py

Requires:
    - FOOTBALL_DATA_API_KEY in env (.env file)
    - SQLite DB initialized via `alembic upgrade head`

Output:
    [PL]  Premier League         → 20 teams (Football-Data)
    [PD]  La Liga                → 20 teams (Football-Data)
    [EC1] LigaPro Serie A        → 16 teams (SofaScore)
    ...
"""

import sys
from pathlib import Path

# Ensure backend/ on path when run as script
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from data.cache import CacheService
from data.fetchers.base import FetchError
from data.fetchers.football_data import FootballDataFetcher
from data.fetchers.sofascore import SofaScoreFetcher, TOURNAMENT_IDS
from data.parsers import ParsedTeam
from data.parsers.football_data_parser import parse_competition_teams as parse_fd
from data.parsers.sofascore_parser import parse_season_teams as parse_sofa
from db.database import SessionLocal
from db.models import Team


# Which leagues to seed and from which source.
# Football-Data: European leagues (cleaner data, has odds for backtesting)
# SofaScore: Liga Pro Ecuador + Copa Libertadores (only source)
SEED_PLAN = [
    # (league_code, source, source_specific_id)
    ("PL", "football_data", "PL"),
    ("PD", "football_data", "PD"),
    ("BL1", "football_data", "BL1"),
    ("SA", "football_data", "SA"),
    ("FL1", "football_data", "FL1"),
    ("CL", "football_data", "CL"),
    ("EC1", "sofascore", TOURNAMENT_IDS["EC1"]),
    ("LIB", "sofascore", TOURNAMENT_IDS["LIB"]),
]


def upsert_teams(session: Session, teams: list[ParsedTeam]) -> tuple[int, int]:
    """Insert teams idempotently. Returns (inserted, skipped) counts."""
    inserted = 0
    skipped = 0

    for team in teams:
        stmt = sqlite_insert(Team).values(
            name=team.name,
            slug=team.slug,
            league=team.league,
            country=team.country,
            football_data_id=team.football_data_id,
            sofascore_id=team.sofascore_id,
        )
        # SQLite: INSERT OR IGNORE on conflict with (slug, league)
        stmt = stmt.on_conflict_do_nothing(index_elements=["slug", "league"])
        result = session.execute(stmt)
        if result.rowcount > 0:
            inserted += 1
        else:
            skipped += 1

    session.commit()
    return inserted, skipped


def seed_football_data_league(
    session: Session, fetcher: FootballDataFetcher,
    league_code: str, fd_code: str,
) -> tuple[int, int, int]:
    """Fetch + parse + upsert teams for a Football-Data competition.

    Returns (total, inserted, skipped).
    """
    payload = fetcher.get_competition_teams(fd_code)
    teams = parse_fd(payload, league_code)
    inserted, skipped = upsert_teams(session, teams)
    return len(teams), inserted, skipped


def seed_sofascore_league(
    session: Session, fetcher: SofaScoreFetcher,
    league_code: str, tournament_id: int,
) -> tuple[int, int, int]:
    """Fetch + parse + upsert teams for a SofaScore tournament.

    Returns (total, inserted, skipped).
    """
    seasons_payload = fetcher.get_tournament_seasons(tournament_id)
    seasons = seasons_payload.get("seasons", [])
    if not seasons:
        return 0, 0, 0
    latest_season_id = seasons[0]["id"]

    teams_payload = fetcher.get_season_teams(tournament_id, latest_season_id)
    teams = parse_sofa(teams_payload, league_code)
    inserted, skipped = upsert_teams(session, teams)
    return len(teams), inserted, skipped


def main() -> int:
    """Run the seed. Returns exit code (0=success, 1=any league failed)."""
    load_dotenv(BACKEND_DIR / ".env")

    session = SessionLocal()
    cache = CacheService(session)
    try:
        fd_fetcher = FootballDataFetcher(cache)
    except ValueError as e:
        print(f"❌ {e}")
        return 1
    sofa_fetcher = SofaScoreFetcher(cache)

    print("\n" + "=" * 70)
    print("SEEDING TEAMS — Rinnegan Bets")
    print("=" * 70 + "\n")

    total_inserted = 0
    failures: list[str] = []

    for league_code, source, source_id in SEED_PLAN:
        try:
            if source == "football_data":
                total, inserted, skipped = seed_football_data_league(
                    session, fd_fetcher, league_code, source_id
                )
            elif source == "sofascore":
                total, inserted, skipped = seed_sofascore_league(
                    session, sofa_fetcher, league_code, source_id
                )
            else:
                raise ValueError(f"Unknown source: {source}")

            status = "✅" if total > 0 else "⚠️"
            print(
                f"  {status} [{league_code:4s}] {source:14s} "
                f"→ {total} teams (inserted {inserted}, skipped {skipped})"
            )
            total_inserted += inserted

        except FetchError as e:
            print(f"  ❌ [{league_code:4s}] {source:14s} → fetch failed: {e}")
            failures.append(league_code)
        except Exception as e:
            print(f"  ❌ [{league_code:4s}] {source:14s} → unexpected: {e}")
            failures.append(league_code)

    print("\n" + "=" * 70)
    print(f"Total teams inserted: {total_inserted}")
    print(f"Total teams in DB: {session.query(Team).count()}")
    if failures:
        print(f"Failed leagues: {failures}")
        print("=" * 70 + "\n")
        return 1
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
