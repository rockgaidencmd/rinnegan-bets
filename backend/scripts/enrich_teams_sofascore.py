#!/usr/bin/env python3
"""Enrich teams in DB with sofascore_id by searching SofaScore by name.

Required so seed_matches.py can fetch match stats (only SofaScore has xG).
Most European teams loaded via Football-Data lack sofascore_id initially.

Usage:
    python scripts/enrich_teams_sofascore.py

Idempotent: skips teams that already have sofascore_id.
"""

import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import requests
from sqlalchemy import select

from core.leagues import LEAGUES
from db.database import SessionLocal
from db.models import Team


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
SEARCH_URL = "https://api.sofascore.com/api/v1/search/all"
SLEEP_SECONDS = 0.25  # Respect rate limits


# Map our internal league code → search-helper country.
# "Europe" and "South America" are too broad for SofaScore search disambiguation,
# so we return None for them and the search falls back to name-only matching.
_NON_NATIONAL_COUNTRIES = {"Europe", "South America"}


def _country_for_search(league_code: str) -> str | None:
    info = LEAGUES.get(league_code)
    if info is None or info.country in _NON_NATIONAL_COUNTRIES:
        return None
    return info.country


LEAGUE_COUNTRY = {code: _country_for_search(code) for code in LEAGUES}


# Football-Data uses official full names; SofaScore uses common short names.
# Map known mismatches here so search finds them on retry.
NAME_ALIASES = {
    "FC Internazionale Milano": "Inter",
    "Sport Lisboa e Benfica": "Benfica",
    "PAE Olympiakos SFP": "Olympiakos",
    "FC St. Pauli 1910": "St. Pauli",
    "Stade Rennais FC 1901": "Stade Rennais",
    "Qarabağ Ağdam FK": "Qarabag FK",
    "FK Bodø/Glimt": "Bodo/Glimt",
}


def _query_search(query: str) -> list[dict]:
    """Hit SofaScore search endpoint, return list of team candidates."""
    try:
        response = requests.get(
            SEARCH_URL,
            params={"q": query},
            headers={"User-Agent": USER_AGENT},
            timeout=5,
        )
        if response.status_code != 200:
            return []
        results = response.json().get("results", [])
        return [r for r in results if r.get("type") == "team"]
    except requests.RequestException:
        return []


def _best_match(
    candidates: list[dict], query: str, expected_country: str | None
) -> int | None:
    """Pick the best matching team from search results."""
    if not candidates:
        return None

    # Tier 1: exact name + country match
    if expected_country:
        for r in candidates:
            ent = r.get("entity", {})
            if (
                ent.get("name", "").lower() == query.lower()
                and ent.get("country", {}).get("name") == expected_country
            ):
                return ent["id"]

    # Tier 2: substring match + country
    if expected_country:
        for r in candidates:
            ent = r.get("entity", {})
            name = ent.get("name", "").lower()
            if (
                (query.lower() in name or name in query.lower())
                and ent.get("country", {}).get("name") == expected_country
            ):
                return ent["id"]

    # Tier 3: exact name regardless of country (CL/LIB cases)
    for r in candidates:
        ent = r.get("entity", {})
        if ent.get("name", "").lower() == query.lower():
            return ent["id"]

    # Tier 4: top result (last resort)
    return candidates[0]["entity"]["id"]


def search_team(name: str, expected_country: str | None) -> int | None:
    """Search SofaScore for a team. Tries the full name first, then alias if mapped.

    Returns sofascore_id if found, else None.
    """
    # Build search attempts: full name + alias if known
    attempts = [name]
    if name in NAME_ALIASES:
        attempts.append(NAME_ALIASES[name])

    for query in attempts:
        candidates = _query_search(query)
        sofa_id = _best_match(candidates, query, expected_country)
        if sofa_id:
            return sofa_id
        time.sleep(SLEEP_SECONDS)  # rate-limit between retries

    return None


def main() -> int:
    session = SessionLocal()

    teams_to_enrich = session.execute(
        select(Team).where(Team.sofascore_id.is_(None))
    ).scalars().all()

    print(f"\n{'=' * 70}")
    print(f"ENRICHING {len(teams_to_enrich)} teams with sofascore_id")
    print(f"{'=' * 70}\n")

    found = 0
    missing = 0
    errors = 0

    for i, team in enumerate(teams_to_enrich, 1):
        country = LEAGUE_COUNTRY.get(team.league)
        try:
            sofa_id = search_team(team.name, country)
        except Exception as e:
            print(f"  ❌ [{i:3d}/{len(teams_to_enrich)}] {team.name}: {e}")
            errors += 1
            time.sleep(SLEEP_SECONDS)
            continue

        if sofa_id:
            team.sofascore_id = sofa_id
            session.commit()
            found += 1
            print(f"  ✅ [{i:3d}/{len(teams_to_enrich)}] [{team.league:4s}] {team.name:40s} → sofa_id={sofa_id}")
        else:
            missing += 1
            print(f"  ⚠️  [{i:3d}/{len(teams_to_enrich)}] [{team.league:4s}] {team.name:40s} → NOT FOUND")

        time.sleep(SLEEP_SECONDS)

    session.close()

    print(f"\n{'=' * 70}")
    print(f"Result: {found} enriched, {missing} not found, {errors} errors")
    print(f"{'=' * 70}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
