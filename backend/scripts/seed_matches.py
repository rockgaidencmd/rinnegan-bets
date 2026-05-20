#!/usr/bin/env python3
"""Seed the matches table with recent finished games + xG/possession stats.

For each team with sofascore_id, fetches last N matches and merges
detailed statistics (xG, possession, corners, etc).

Usage:
    python scripts/seed_matches.py [--per-team N]

Defaults to last 5 matches per team. With ~60 teams enriched, that's
~300 raw matches, deduplicated to ~150-200 unique fixtures.

Idempotent: existing matches (by source+external_id) are skipped.
"""

import argparse
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from data.cache import CacheService
from data.fetchers.base import FetchError
from data.fetchers.sofascore import SofaScoreFetcher
from data.parsers import ParsedMatch
from data.parsers.sofascore_match_parser import (
    merge_statistics,
    parse_team_performance,
)
from db.database import SessionLocal
from db.models import Match, Team


SLEEP_SECONDS = 0.2  # Between API calls — respect rate limits


def find_team_id_by_sofascore_id(
    session: Session, sofa_id: int, preferred_league: str | None = None
) -> int | None:
    """Map a sofascore_id back to our internal team.id.

    A team can appear in multiple leagues (e.g., Arsenal in PL and CL).
    Prefer the row matching the match's league; otherwise take any row.
    """
    if preferred_league:
        team = session.execute(
            select(Team).where(
                Team.sofascore_id == sofa_id,
                Team.league == preferred_league,
            )
        ).scalar_one_or_none()
        if team:
            return team.id

    # Fallback: any team with this sofascore_id (same conceptual entity)
    team = session.execute(
        select(Team).where(Team.sofascore_id == sofa_id).limit(1)
    ).scalars().first()
    return team.id if team else None


def upsert_match(session: Session, match: ParsedMatch) -> bool:
    """Insert match if new. Returns True if inserted, False if duplicate.

    Skips matches where we can't find both teams in our DB.
    """
    home_id = find_team_id_by_sofascore_id(
        session, match.home_team_sofascore_id, preferred_league=match.league
    )
    away_id = find_team_id_by_sofascore_id(
        session, match.away_team_sofascore_id, preferred_league=match.league
    )
    if not home_id or not away_id:
        return False

    stmt = sqlite_insert(Match).values(
        home_team_id=home_id,
        away_team_id=away_id,
        league=match.league,
        match_date=match.match_date,
        home_goals=match.home_goals,
        away_goals=match.away_goals,
        result=match.result,
        home_xg=match.home_xg,
        away_xg=match.away_xg,
        home_possession=match.home_possession,
        away_possession=match.away_possession,
        home_shots_on_target=match.home_shots_on_target,
        away_shots_on_target=match.away_shots_on_target,
        home_corners=match.home_corners,
        away_corners=match.away_corners,
        home_yellow_cards=match.home_yellow_cards,
        away_yellow_cards=match.away_yellow_cards,
        source=match.source,
        external_id=match.external_id,
        fetched_at=datetime.now(timezone.utc),
    )
    stmt = stmt.on_conflict_do_nothing(index_elements=["source", "external_id"])
    result = session.execute(stmt)
    session.commit()
    return result.rowcount > 0


def seed_matches_for_team(
    session: Session, fetcher: SofaScoreFetcher,
    team: Team, per_team_limit: int,
) -> tuple[int, int]:
    """Fetch and persist recent matches for one team. Returns (fetched, inserted).

    Uses the /performance endpoint which returns truly recent matches
    (current season), not the prior-season data /events/last/0 returns.
    Each match's `league` is resolved from its actual tournament — so a
    Bayern match in Champions League gets league=CL, not BL1.
    """
    try:
        perf_payload = fetcher.get_team_performance(team.sofascore_id)
    except FetchError as e:
        print(f"    ⚠️  Could not fetch performance for {team.name}: {e}")
        return 0, 0

    parsed = parse_team_performance(perf_payload)
    parsed = parsed[:per_team_limit]

    inserted = 0
    for match in parsed:
        try:
            stats_payload = fetcher.get_event_statistics(int(match.external_id))
            time.sleep(SLEEP_SECONDS)
            enriched = merge_statistics(match, stats_payload)
        except FetchError:
            # Stats failed but we still have basic match data — persist anyway
            enriched = match

        if upsert_match(session, enriched):
            inserted += 1

    return len(parsed), inserted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-team", type=int, default=5,
                        help="Max matches to fetch per team (default: 5)")
    parser.add_argument("--league", type=str, default=None,
                        help="Only process teams from this league code")
    args = parser.parse_args()

    load_dotenv(BACKEND_DIR / ".env")

    session = SessionLocal()
    cache = CacheService(session)
    fetcher = SofaScoreFetcher(cache)

    query = select(Team).where(Team.sofascore_id.is_not(None))
    if args.league:
        query = query.where(Team.league == args.league)
    teams = session.execute(query).scalars().all()

    print(f"\n{'=' * 70}")
    print(f"SEEDING MATCHES — {len(teams)} teams, up to {args.per_team} per team")
    print(f"{'=' * 70}\n")

    total_fetched = 0
    total_inserted = 0

    for i, team in enumerate(teams, 1):
        fetched, inserted = seed_matches_for_team(
            session, fetcher, team, args.per_team
        )
        total_fetched += fetched
        total_inserted += inserted
        print(
            f"  [{i:3d}/{len(teams)}] [{team.league:4s}] {team.name:35s} "
            f"→ {fetched} fetched, {inserted} new"
        )
        time.sleep(SLEEP_SECONDS)

    matches_in_db = session.query(Match).count()
    session.close()

    print(f"\n{'=' * 70}")
    print(f"Total fetched: {total_fetched}")
    print(f"Total new inserts: {total_inserted}")
    print(f"Total matches in DB: {matches_in_db}")
    print(f"{'=' * 70}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
