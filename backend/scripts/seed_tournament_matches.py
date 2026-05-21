#!/usr/bin/env python3
"""Seed matches for a SPECIFIC tournament by iterating all its events.

Use this for short tournaments (CL, LIB) where seed_matches.py
(per-team iteration) misses fixtures because each team only plays
a handful of games there.

Usage:
    python scripts/seed_tournament_matches.py --league CL
    python scripts/seed_tournament_matches.py --league LIB --pages 3

Pages: each page returns ~30 events from the season, newest first.
Default 3 pages = up to ~90 matches per tournament.

Idempotent: existing matches (by source+external_id) are skipped.
"""

import argparse
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

from core.leagues import LEAGUES
from data.cache import CacheService
from data.fetchers.base import FetchError
from data.fetchers.sofascore import SofaScoreFetcher
from data.parsers.sofascore_match_parser import (
    merge_statistics,
    parse_team_performance,
)
from db.database import SessionLocal
from db.models import Match
from scripts.seed_matches import upsert_match


SLEEP_SECONDS = 0.2


def get_latest_season_id(fetcher: SofaScoreFetcher, tournament_id: int) -> int | None:
    """First season returned by /seasons is the most recent."""
    seasons = fetcher.get_tournament_seasons(tournament_id).get("seasons", [])
    return seasons[0]["id"] if seasons else None


def _iter_events_by_page(
    fetcher: SofaScoreFetcher, tournament_id: int, season_id: int, pages: int,
):
    """Yield event payloads from /events/last/N pagination."""
    for page in range(pages):
        try:
            payload = fetcher.get_tournament_events(tournament_id, season_id, page)
        except FetchError:
            return
        events = payload.get("events", [])
        if not events:
            return
        yield page, payload


def _iter_events_by_round(
    fetcher: SofaScoreFetcher, tournament_id: int, season_id: int, max_rounds: int,
):
    """Yield event payloads from /events/round/N — cup tournament fallback."""
    for round_num in range(1, max_rounds + 1):
        try:
            payload = fetcher.get_tournament_round_events(tournament_id, season_id, round_num)
        except FetchError:
            continue  # Some rounds may not exist yet — keep trying others
        if payload.get("events"):
            yield round_num, payload


def seed_tournament(
    session, fetcher: SofaScoreFetcher, league_code: str, pages: int,
) -> tuple[int, int]:
    """Returns (fetched_events, inserted_matches).

    Strategy: try /events/last/N pagination first (works for league-phase
    tournaments). If first page returns nothing, fall back to /events/round/N
    iteration (cup tournaments in early stages).
    """
    info = LEAGUES.get(league_code)
    if info is None:
        raise ValueError(f"Unknown league: {league_code}")

    season_id = get_latest_season_id(fetcher, info.sofascore_id)
    if season_id is None:
        print(f"  ⚠️  No seasons found for {league_code}")
        return 0, 0

    print(f"  Tournament {info.name} ({info.sofascore_id}) season {season_id}")

    iterator = _iter_events_by_page(fetcher, info.sofascore_id, season_id, pages)
    fetched_total = 0
    inserted_total = 0

    for label, payload in iterator:
        fetched, inserted = _persist_events(session, fetcher, payload)
        fetched_total += fetched
        inserted_total += inserted
        print(f"  Page {label}: {fetched} events, {inserted} new")
        time.sleep(SLEEP_SECONDS)

    if fetched_total == 0:
        # Fallback to round-by-round (cup tournaments)
        print(f"  No pagination data — trying round-by-round")
        iterator = _iter_events_by_round(fetcher, info.sofascore_id, season_id, max_rounds=20)
        for round_num, payload in iterator:
            fetched, inserted = _persist_events(session, fetcher, payload)
            fetched_total += fetched
            inserted_total += inserted
            print(f"  Round {round_num}: {fetched} events, {inserted} new")
            time.sleep(SLEEP_SECONDS)

    return fetched_total, inserted_total


def _persist_events(session, fetcher: SofaScoreFetcher, payload: dict) -> tuple[int, int]:
    """Parse + enrich with stats + upsert. Returns (fetched, inserted)."""
    parsed = parse_team_performance(payload)
    inserted = 0
    for match in parsed:
        try:
            stats_payload = fetcher.get_event_statistics(int(match.external_id))
            time.sleep(SLEEP_SECONDS)
            enriched = merge_statistics(match, stats_payload)
        except FetchError:
            enriched = match
        if upsert_match(session, enriched):
            inserted += 1
    return len(parsed), inserted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--league", required=True,
        help=f"League code (one of: {', '.join(sorted(LEAGUES.keys()))})",
    )
    parser.add_argument(
        "--pages", type=int, default=3,
        help="How many pages of events to pull (default: 3, ~90 matches)",
    )
    args = parser.parse_args()

    load_dotenv(BACKEND_DIR / ".env")

    session = SessionLocal()
    cache = CacheService(session)
    fetcher = SofaScoreFetcher(cache)

    print(f"\n{'=' * 70}")
    print(f"SEEDING TOURNAMENT — {args.league} ({args.pages} pages)")
    print(f"{'=' * 70}\n")

    fetched, inserted = seed_tournament(session, fetcher, args.league, args.pages)

    total_in_db = session.query(Match).filter(Match.league == args.league).count()
    session.close()

    print(f"\n{'=' * 70}")
    print(f"Fetched: {fetched} events")
    print(f"Inserted: {inserted} new matches")
    print(f"Total {args.league} in DB: {total_in_db}")
    print(f"{'=' * 70}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
