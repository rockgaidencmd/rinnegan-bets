#!/usr/bin/env python3
"""Seed finished matches for one or all supported leagues.

Iterates a tournament's events (paginated for league-phase tournaments,
round-by-round for cup tournaments still in early stages). For each event:

  1. Auto-create home/away teams in DB if their sofascore_id isn't seeded yet.
  2. Fetch per-match stats (xG, possession, etc).
  3. Upsert the match row (idempotent on source+external_id).

Usage:
    python scripts/seed_matches.py --league EC1
    python scripts/seed_matches.py --all              # all configured leagues
    python scripts/seed_matches.py --league CL --max-pages 5

Defaults to iterating until SofaScore returns an empty page (no fixed limit).
"""

import argparse
import logging
import sys
import time
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from core.leagues import LEAGUES, LeagueInfo
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


logger = logging.getLogger("seed_matches")

# Sleep between SofaScore calls — respect rate limits.
SLEEP_SECONDS = 0.2
# Hard ceiling on pages so a runaway loop can't hammer the API for an hour.
DEFAULT_MAX_PAGES = 20
# Max rounds to try when paginated endpoint returns nothing (cup tournaments).
MAX_ROUNDS = 30


# ─────────────────────────────────────────────────────────────────────────────
# Fetching: yield event payloads — pure iteration, no DB writes
# ─────────────────────────────────────────────────────────────────────────────

def _iter_pages(
    fetcher: SofaScoreFetcher, tournament_id: int, season_id: int, max_pages: int,
) -> Generator[tuple[str, dict], None, None]:
    """Yield (label, payload) from /events/last/{N} until empty or max_pages."""
    for page in range(max_pages):
        try:
            payload = fetcher.get_tournament_events(tournament_id, season_id, page)
        except FetchError:
            return
        if not payload.get("events"):
            return
        yield f"page {page}", payload


def _iter_rounds(
    fetcher: SofaScoreFetcher, tournament_id: int, season_id: int, max_rounds: int,
) -> Generator[tuple[str, dict], None, None]:
    """Yield (label, payload) from /events/round/{N} — cup tournament fallback."""
    for round_num in range(1, max_rounds + 1):
        try:
            payload = fetcher.get_tournament_round_events(tournament_id, season_id, round_num)
        except FetchError:
            continue
        if payload.get("events"):
            yield f"round {round_num}", payload


def _iter_tournament_events(
    fetcher: SofaScoreFetcher, tournament_id: int, season_id: int, max_pages: int,
) -> Generator[tuple[str, dict], None, None]:
    """Try paginated first; fall back to round-by-round if no pages had data."""
    had_any = False
    for label, payload in _iter_pages(fetcher, tournament_id, season_id, max_pages):
        had_any = True
        yield label, payload

    if not had_any:
        logger.info("  no paginated data — falling back to round iteration")
        yield from _iter_rounds(fetcher, tournament_id, season_id, MAX_ROUNDS)


# ─────────────────────────────────────────────────────────────────────────────
# DB writes: idempotent upserts + auto-enrich teams
# ─────────────────────────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace(".", "").replace("'", "")


def _ensure_team_exists(
    session: Session, sofascore_id: int, name: str, league: str,
) -> int:
    """Look up team by sofascore_id; create it if missing. Returns team.id.

    Why this exists: SofaScore returns matches involving teams we may not
    have seeded yet (e.g. an EC1 team plays an LIB knockout). Instead of
    skipping the match, we create the team on demand. Idempotent — second
    call with the same (slug, league) hits the UNIQUE constraint and reuses.
    """
    team = session.query(Team).filter(Team.sofascore_id == sofascore_id).first()
    if team:
        return team.id

    slug = _slugify(name)
    # Use UPSERT to handle the rare race where two events name the same new team.
    stmt = sqlite_insert(Team).values(
        name=name, slug=slug, league=league,
        country=None, sofascore_id=sofascore_id,
    )
    stmt = stmt.on_conflict_do_nothing(index_elements=["slug", "league"])
    session.execute(stmt)
    session.commit()

    team = session.query(Team).filter(Team.sofascore_id == sofascore_id).first()
    if team:
        return team.id
    # The (slug, league) collision case — pick by slug+league instead
    team = session.query(Team).filter(Team.slug == slug, Team.league == league).first()
    if team is None:
        raise RuntimeError(f"Failed to create or find team: {name} (sofascore_id={sofascore_id})")
    return team.id


def _upsert_match(session: Session, match: ParsedMatch) -> bool:
    """Insert match row. Returns True if new, False if it already existed.

    Idempotent: re-running won't create duplicates thanks to the
    UNIQUE(source, external_id) constraint.
    """
    home_id = _ensure_team_exists(
        session, match.home_team_sofascore_id, match.home_team_name, match.league,
    )
    away_id = _ensure_team_exists(
        session, match.away_team_sofascore_id, match.away_team_name, match.league,
    )

    stmt = sqlite_insert(Match).values(
        home_team_id=home_id, away_team_id=away_id,
        league=match.league, match_date=match.match_date,
        home_goals=match.home_goals, away_goals=match.away_goals, result=match.result,
        home_xg=match.home_xg, away_xg=match.away_xg,
        home_possession=match.home_possession, away_possession=match.away_possession,
        home_shots_on_target=match.home_shots_on_target,
        away_shots_on_target=match.away_shots_on_target,
        home_corners=match.home_corners, away_corners=match.away_corners,
        home_yellow_cards=match.home_yellow_cards, away_yellow_cards=match.away_yellow_cards,
        source=match.source, external_id=match.external_id,
        fetched_at=datetime.now(timezone.utc),
    )
    stmt = stmt.on_conflict_do_nothing(index_elements=["source", "external_id"])
    result = session.execute(stmt)
    session.commit()
    return result.rowcount > 0


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration: combine fetch + parse + write
# ─────────────────────────────────────────────────────────────────────────────

def _persist_events(session: Session, fetcher: SofaScoreFetcher, payload: dict) -> tuple[int, int]:
    parsed = parse_team_performance(payload)
    inserted = 0
    for match in parsed:
        try:
            stats_payload = fetcher.get_event_statistics(int(match.external_id))
            time.sleep(SLEEP_SECONDS)
            enriched = merge_statistics(match, stats_payload)
        except FetchError:
            enriched = match
        if _upsert_match(session, enriched):
            inserted += 1
    return len(parsed), inserted


def seed_league(
    session: Session, fetcher: SofaScoreFetcher,
    info: LeagueInfo, max_pages: int,
) -> tuple[int, int]:
    """Returns (events_fetched, matches_inserted)."""
    seasons = fetcher.get_tournament_seasons(info.sofascore_id).get("seasons", [])
    if not seasons:
        logger.warning("  no seasons found for %s", info.code)
        return 0, 0

    season_id = seasons[0]["id"]
    logger.info("  %s (sofa=%d) season %d", info.name, info.sofascore_id, season_id)

    total_fetched = 0
    total_inserted = 0
    for label, payload in _iter_tournament_events(fetcher, info.sofascore_id, season_id, max_pages):
        fetched, inserted = _persist_events(session, fetcher, payload)
        total_fetched += fetched
        total_inserted += inserted
        logger.info("  %s: %d events, %d new", label, fetched, inserted)
        time.sleep(SLEEP_SECONDS)

    return total_fetched, total_inserted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--league", help=f"One of: {', '.join(sorted(LEAGUES))}")
    group.add_argument("--all", action="store_true", help="Seed every supported league")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES,
                        help=f"Cap on pages per league (default {DEFAULT_MAX_PAGES})")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    load_dotenv(BACKEND_DIR / ".env")

    targets: list[LeagueInfo]
    if args.all:
        targets = sorted(LEAGUES.values(), key=lambda i: i.code)
    else:
        info = LEAGUES.get(args.league)
        if info is None:
            print(f"❌ Unknown league: {args.league}", file=sys.stderr)
            return 2
        targets = [info]

    session = SessionLocal()
    cache = CacheService(session)
    fetcher = SofaScoreFetcher(cache)

    print(f"\n{'=' * 70}")
    print(f"SEEDING — {len(targets)} league(s)")
    print(f"{'=' * 70}\n")

    grand_fetched = 0
    grand_inserted = 0
    for info in targets:
        print(f"[{info.code}] {info.name}")
        fetched, inserted = seed_league(session, fetcher, info, args.max_pages)
        grand_fetched += fetched
        grand_inserted += inserted
        print(f"  → {fetched} fetched, {inserted} new\n")

    matches_in_db = session.query(Match).count()
    teams_in_db = session.query(Team).count()
    session.close()

    print(f"{'=' * 70}")
    print(f"Total fetched: {grand_fetched}")
    print(f"Total new matches: {grand_inserted}")
    print(f"DB now: {matches_in_db} matches, {teams_in_db} teams")
    print(f"{'=' * 70}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
