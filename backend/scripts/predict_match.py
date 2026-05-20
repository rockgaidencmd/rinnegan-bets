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

from core.bankroll.tracker import BankrollTracker
from core.features.extractor import extract_team_features
from core.models.factory import get_model_for_league
from core.types import MatchContext
from db.database import SessionLocal
from db.models import Match, Team


# Leagues where teams from different domestic leagues can legitimately meet
INTERNATIONAL_LEAGUES = {"CL", "LIB"}


def find_teams_by_name(session, name: str) -> list[Team]:
    """Find all team rows matching name (a team can exist in multiple leagues)."""
    teams = session.execute(
        select(Team).where(Team.name.ilike(f"%{name}%"))
    ).scalars().all()
    if not teams:
        raise ValueError(f"Team not found: {name}")
    return teams


def resolve_matchup(
    home_candidates: list[Team], away_candidates: list[Team], force: bool,
) -> tuple[Team, Team, str]:
    """Pick the (home, away, league) tuple that represents a realistic matchup.

    Logic:
      1. If both teams share a league, use that (prefer domestic over CL/LIB).
      2. If they share only an international league (CL/LIB), use that.
      3. If no overlap → real teams that never face each other (Napoli vs Aucas).
         Refuse unless --force is passed.
    """
    home_leagues = {t.league for t in home_candidates}
    away_leagues = {t.league for t in away_candidates}
    shared = home_leagues & away_leagues

    # Prefer domestic shared league over international (CL/LIB)
    domestic_shared = shared - INTERNATIONAL_LEAGUES
    if domestic_shared:
        league = sorted(domestic_shared)[0]
    elif shared:
        league = sorted(shared)[0]
    elif force:
        # User insists — pick home team's primary league for model selection
        league = sorted(home_leagues)[0]
        print(f"⚠️  WARNING: {home_candidates[0].name} ({sorted(home_leagues)}) "
              f"and {away_candidates[0].name} ({sorted(away_leagues)}) "
              f"play in different leagues — they would never meet IRL.")
        print(f"   Using --force: predicting anyway with model for '{league}'.\n")
        # Use the home team in `league`, but for away just pick any row
        home = next(t for t in home_candidates if t.league == league)
        away = away_candidates[0]
        return home, away, league
    else:
        raise ValueError(
            f"\n❌ '{home_candidates[0].name}' (leagues: {sorted(home_leagues)}) "
            f"and '{away_candidates[0].name}' (leagues: {sorted(away_leagues)}) "
            f"don't share any league.\n"
            f"   These teams would never meet in reality.\n"
            f"   Add --force to predict anyway (e.g. for a hypothetical/fantasy matchup)."
        )

    home = next(t for t in home_candidates if t.league == league)
    away = next(t for t in away_candidates if t.league == league)
    return home, away, league


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
    parser.add_argument("--force", action="store_true",
                        help="Predict even if teams don't share a real-world league")
    args = parser.parse_args()

    session = SessionLocal()

    try:
        home_candidates = find_teams_by_name(session, args.home)
        away_candidates = find_teams_by_name(session, args.away)
        home, away, league = resolve_matchup(home_candidates, away_candidates, args.force)
    except ValueError as e:
        print(str(e))
        return 2

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

    # Stake recommendation in real dollars based on bankroll
    tracker = BankrollTracker(session)
    bankroll = tracker.get_available_balance()
    if bankroll > 0:
        recommended_stake = prediction.kelly * bankroll
        print(f"\n  💰 Bankroll disponible: ${bankroll:.2f}")
        print(f"  💵 Stake recomendado (Kelly): ${recommended_stake:.2f}")
        if recommended_stake > args.stake:
            print(f"     (Vas a apostar ${args.stake:.2f} — menos que Kelly. Conservador, OK.)")
        elif recommended_stake < args.stake:
            print(f"     ⚠️  Vas a apostar ${args.stake:.2f} — MÁS que Kelly. Riesgo elevado.")
    else:
        print(f"\n  💰 Bankroll vacío. Inicialízalo con: python scripts/bankroll.py deposit 150")

    print(f"\nComponent breakdown:")
    for name, value in prediction.reasoning["components"].items():
        weight = prediction.reasoning["weights"][name]
        contribution = value * weight
        print(f"  {name:18s}  signal={value:+.2f}  weight={weight:.2f}  → {contribution:+.3f}")

    session.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
