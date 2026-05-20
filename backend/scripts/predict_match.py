#!/usr/bin/env python3
"""Quick prediction script — uses real data from BD to predict a hypothetical match.

Usage:
    python scripts/predict_match.py "Independiente del Valle" "LDU" --quota 2.30 --stake 10
    python scripts/predict_match.py "Arsenal FC" "Manchester City FC" --quota 3.50 --stake 20
"""

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import or_, select

from core.features.extractor import extract_team_features
from core.models.factory import get_model_for_league
from core.types import MatchContext
from db.database import SessionLocal
from db.models import Match, Team


def find_team(session, name: str) -> Team:
    """Find first team matching name (case-insensitive)."""
    team = session.execute(
        select(Team).where(Team.name.ilike(f"%{name}%")).limit(1)
    ).scalar_one_or_none()
    if not team:
        raise ValueError(f"Team not found: {name}")
    return team


def get_last_matches(session, team_id: int, limit: int = 10) -> list[Match]:
    """Last N finished matches for a team (home or away)."""
    return session.execute(
        select(Match)
        .where(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))
        .where(Match.home_goals.is_not(None))
        .order_by(Match.match_date.desc())
        .limit(limit)
    ).scalars().all()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("home", help="Home team name (case-insensitive substring)")
    parser.add_argument("away", help="Away team name")
    parser.add_argument("--quota", type=float, required=True, help="Bookmaker odds")
    parser.add_argument("--stake", type=float, default=10.0, help="Stake amount")
    parser.add_argument("--importance", default="normal",
                        choices=["final", "clasif", "normal", "calendario"])
    parser.add_argument("--home-absences", action="store_true")
    parser.add_argument("--away-absences", action="store_true")
    args = parser.parse_args()

    session = SessionLocal()

    home = find_team(session, args.home)
    away = find_team(session, args.away)
    league = home.league if home.league == away.league else home.league

    print(f"\n{'=' * 70}")
    print(f"PREDICTION: {home.name}  vs  {away.name}")
    print(f"League: {league}  |  Quota: {args.quota}  |  Stake: ${args.stake}")
    print(f"{'=' * 70}\n")

    home_matches = get_last_matches(session, home.id)
    away_matches = get_last_matches(session, away.id)
    print(f"Data: {len(home_matches)} home matches, {len(away_matches)} away matches\n")

    home_features = extract_team_features(home_matches, home.id)
    away_features = extract_team_features(away_matches, away.id)

    print(f"--- {home.name} (last {home_features.matches_analyzed}) ---")
    print(f"  Form: {home_features.wins}W {home_features.draws}D {home_features.losses}L"
          f"  → {home_features.form_score:.0f}/100")
    print(f"  Goals: {home_features.avg_goals_for:.2f} vs {home_features.avg_goals_against:.2f}")
    if home_features.avg_xg_for:
        print(f"  xG: {home_features.avg_xg_for:.2f} vs {home_features.avg_xg_against:.2f}")
    if home_features.avg_possession:
        print(f"  Possession: {home_features.avg_possession:.1f}%")

    print(f"\n--- {away.name} (last {away_features.matches_analyzed}) ---")
    print(f"  Form: {away_features.wins}W {away_features.draws}D {away_features.losses}L"
          f"  → {away_features.form_score:.0f}/100")
    print(f"  Goals: {away_features.avg_goals_for:.2f} vs {away_features.avg_goals_against:.2f}")
    if away_features.avg_xg_for:
        print(f"  xG: {away_features.avg_xg_for:.2f} vs {away_features.avg_xg_against:.2f}")

    print()
    context = MatchContext(
        importance=args.importance,
        home_key_absences=args.home_absences,
        away_key_absences=args.away_absences,
    )
    model = get_model_for_league(league)
    prediction = model.predict(home_features, away_features, context, args.quota, args.stake)

    print(f"{'=' * 70}")
    print(f"VERDICT: {prediction.verdict.verdict.upper()}")
    print(f"{'=' * 70}")
    print(f"  Model: {prediction.model_version}")
    print(f"  Pre-score: {prediction.pre_score:.1f}/100")
    print(f"  Implied prob (market): {prediction.implied_prob:.2%}")
    print(f"  My prob (blended): {prediction.my_prob:.2%}")
    print(f"  Edge: {(prediction.my_prob - prediction.implied_prob):+.2%}")
    print(f"  EV: ${prediction.ev:+.2f} on ${prediction.stake} stake")
    print(f"  Kelly: {prediction.kelly:.1%} of bankroll")
    print(f"  Reason: {prediction.verdict.reason}")

    print(f"\nComponent breakdown:")
    for name, value in prediction.reasoning["components"].items():
        weight = prediction.reasoning["weights"][name]
        contribution = value * weight
        print(f"  {name:18s}  signal={value:+.2f}  weight={weight:.2f}  → {contribution:+.3f}")

    session.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
