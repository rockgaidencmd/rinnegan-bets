#!/usr/bin/env python3
"""Compare multiple matchups in a summary table.

Edit MATCHUPS below to add your own. Then:
    python evaluations/compare_matchups.py
    python evaluations/compare_matchups.py > evaluations/runs/$(date +%Y-%m-%d).txt
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import or_, select

from core.bankroll.tracker import BankrollTracker
from core.features.extractor import extract_team_features
from core.models.factory import get_model_for_league
from core.types import MatchContext
from data.team_search import TeamSearchError, find_teams_by_name, resolve_matchup
from db.database import SessionLocal
from db.models import Match, Team


# (home_name, away_name, quota, importance)
# Edit this list to compare your own matchups.
MATCHUPS = [
    # Europa
    ("Liverpool", "Manchester United", 1.85, "normal"),
    ("Arsenal", "Manchester City", 2.50, "clasif"),
    ("Barcelona", "Real Madrid", 2.40, "clasif"),
    ("Napoli", "Inter", 2.20, "normal"),
    ("Bayern", "Borussia Dortmund", 1.55, "clasif"),
    # Ecuador
    ("Independiente del Valle", "LDU", 2.30, "clasif"),
    ("Barcelona SC", "Emelec", 2.10, "clasif"),
    ("Aucas", "Mushuc Runa", 1.95, "normal"),
    # Internacional
    ("Real Madrid", "Liverpool", 2.10, "clasif"),
]


VERDICT_ICONS = {"apostar": "🟢", "esperar": "🟡", "no_apostar": "🔴"}


def find_shared_league(home_name: str, away_name: str, session) -> tuple[Team, Team, str] | None:
    """Wrapper that returns None instead of raising — convenient for batch mode."""
    try:
        home_rows = find_teams_by_name(session, home_name)
        away_rows = find_teams_by_name(session, away_name)
        return resolve_matchup(home_rows, away_rows, force=False)
    except TeamSearchError:
        return None


def get_last_matches(session, team_id: int, limit: int = 10):
    return session.execute(
        select(Match)
        .where(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))
        .where(Match.home_goals.is_not(None))
        .order_by(Match.match_date.desc())
        .limit(limit)
    ).scalars().all()


def main() -> int:
    session = SessionLocal()
    tracker = BankrollTracker(session)
    bankroll = tracker.get_available_balance()

    print(f"\n{'═' * 90}")
    print(f"  COMPARACIÓN DE PREDICCIONES — Bankroll: ${bankroll:.2f}")
    print(f"{'═' * 90}\n")
    print(f"  {'Verdict':<5} {'Matchup':<46} {'Quota':>6} {'Edge':>7} {'EV ($10)':>9} {'Stake $':>8}")
    print(f"  {'-' * 88}")

    results = []
    for home_name, away_name, quota, importance in MATCHUPS:
        matchup = find_shared_league(home_name, away_name, session)
        if matchup is None:
            print(f"  ❌    {home_name} vs {away_name:<35}  → no shared league, skipped")
            continue

        home, away, league = matchup
        home_matches = get_last_matches(session, home.id)
        away_matches = get_last_matches(session, away.id)
        home_feat = extract_team_features(home_matches, home.id)
        away_feat = extract_team_features(away_matches, away.id)

        context = MatchContext(importance=importance)
        model = get_model_for_league(league)
        pred = model.predict(home_feat, away_feat, context, quota, stake=10.0)

        verdict = pred.verdict.verdict
        icon = VERDICT_ICONS[verdict]
        edge = (pred.my_prob - pred.implied_prob) * 100
        stake_kelly = pred.kelly * bankroll if bankroll > 0 else 0

        matchup_str = f"{home.name[:20]} vs {away.name[:20]} ({league})"
        edge_str = f"{edge:+.1f}%"
        ev_str = f"${pred.ev:+.2f}"
        stake_str = f"${stake_kelly:.2f}"

        print(f"  {icon}    {matchup_str:<46} {quota:>6.2f} {edge_str:>7} {ev_str:>9} {stake_str:>8}")
        results.append((verdict, pred.ev))

    # Summary
    print(f"  {'-' * 88}")
    apostar = sum(1 for v, _ in results if v == "apostar")
    esperar = sum(1 for v, _ in results if v == "esperar")
    no = sum(1 for v, _ in results if v == "no_apostar")
    total_ev = sum(ev for _, ev in results if ev > 0)

    print(f"\n  Total: {len(results)} matchups analizados")
    print(f"  🟢 APOSTAR: {apostar}  |  🟡 ESPERAR: {esperar}  |  🔴 NO APOSTAR: {no}")
    print(f"  EV total (solo positivos, $10 stake): ${total_ev:+.2f}")
    print(f"\n{'═' * 90}\n")

    session.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
