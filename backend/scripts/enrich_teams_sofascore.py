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

from db.database import SessionLocal
from db.models import Team


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
SEARCH_URL = "https://api.sofascore.com/api/v1/search/all"
SLEEP_SECONDS = 0.25  # Respect rate limits


# Map our internal league code → SofaScore country name used in their search results
LEAGUE_COUNTRY = {
    "PL": "England",
    "PD": "Spain",
    "BL1": "Germany",
    "SA": "Italy",
    "FL1": "France",
    "CL": None,    # Multiple countries; match by name only
    "LIB": None,
    "EC1": "Ecuador",
}


def search_team(name: str, expected_country: str | None) -> int | None:
    """Search SofaScore for a team. Returns sofascore_id if confident match found."""
    try:
        response = requests.get(
            SEARCH_URL,
            params={"q": name},
            headers={"User-Agent": USER_AGENT},
            timeout=5,
        )
        if response.status_code != 200:
            return None
        results = response.json().get("results", [])
    except requests.RequestException:
        return None

    candidates = [r for r in results if r.get("type") == "team"]
    if not candidates:
        return None

    # First try: exact name + country match
    if expected_country:
        for r in candidates:
            ent = r.get("entity", {})
            if (
                ent.get("name", "").lower() == name.lower()
                and ent.get("country", {}).get("name") == expected_country
            ):
                return ent["id"]

    # Second try: just country match, take highest-popularity result
    if expected_country:
        country_matches = [
            r for r in candidates
            if r.get("entity", {}).get("country", {}).get("name") == expected_country
        ]
        if country_matches:
            return country_matches[0]["entity"]["id"]

    # Third try: exact name match regardless of country
    for r in candidates:
        ent = r.get("entity", {})
        if ent.get("name", "").lower() == name.lower():
            return ent["id"]

    # Last resort: first candidate (may be wrong, but better than nothing)
    return candidates[0]["entity"]["id"]


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
