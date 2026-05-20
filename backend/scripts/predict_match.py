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
from data.team_search import TeamSearchError, find_teams_by_name, resolve_matchup
from db.database import SessionLocal
from db.models import Match, Team


# --- Constants ---

VERDICT_ICONS = {
    "apostar": "🟢",
    "esperar": "🟡",
    "no_apostar": "🔴",
}

VERDICT_LABELS = {
    "apostar": "APOSTAR",
    "esperar": "ESPERAR",
    "no_apostar": "NO APOSTAR",
}

# Warn if the user's intended stake exceeds Kelly by more than this factor
# (1.2x = 20% more than recommended). Below this margin we stay silent —
# users often round up and that's fine.
KELLY_OVERSTAKE_WARNING_MULT = 1.2

# How many recent matches to pull from BD when extracting team features.
RECENT_MATCHES_FOR_FEATURES = 10


def get_last_matches(session, team_id: int, limit: int = RECENT_MATCHES_FOR_FEATURES) -> list[Match]:
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
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show full breakdown: features, components, weights")
    args = parser.parse_args()

    session = SessionLocal()

    try:
        home_candidates = find_teams_by_name(session, args.home)
        away_candidates = find_teams_by_name(session, args.away)
        home, away, league = resolve_matchup(home_candidates, away_candidates, args.force)
    except TeamSearchError as e:
        print(f"\n❌ {e}\n")
        return 2

    home_matches = get_last_matches(session, home.id)
    away_matches = get_last_matches(session, away.id)
    home_features = extract_team_features(home_matches, home.id)
    away_features = extract_team_features(away_matches, away.id)

    context = MatchContext(
        importance=args.importance,
        home_key_absences=args.home_absences,
        away_key_absences=args.away_absences,
    )
    model = get_model_for_league(league)
    prediction = model.predict(home_features, away_features, context, args.quota, args.stake)

    tracker = BankrollTracker(session)
    bankroll = tracker.get_available_balance()

    if args.verbose:
        _print_verbose(home, away, league, home_features, away_features,
                       prediction, bankroll, args)
    else:
        _print_simple(home, away, league, prediction, bankroll, args)

    session.close()
    return 0


# --- Output formatters ---

def _print_simple(home, away, league, prediction, bankroll, args):
    """Compact, human-friendly output — the default. Orchestrates section printers."""
    bar = "═" * 60
    _print_header(home, away, league, args.quota, bar)
    _print_verdict_line(prediction, home)
    _print_probabilities(prediction, home)
    _print_money_outcome(prediction, home, away, bankroll, args)
    print(f"\n  💡 {_short_reasoning(home, away, prediction)}")
    _print_footer(bar)


def _print_header(home, away, league, quota, bar):
    print(f"\n{bar}")
    print(f"  {home.name}  vs  {away.name}  ({league})")
    print(f"  Mercado: VICTORIA LOCAL ({home.name})")
    print(f"  Cuota: {quota}  →  apuestas a que GANA {home.name}")
    print(f"{bar}\n")


def _print_verdict_line(prediction, home):
    v = prediction.verdict.verdict
    print(f"  {VERDICT_ICONS[v]}  {VERDICT_LABELS[v]}  a {home.name}\n")


def _print_probabilities(prediction, home):
    edge = prediction.my_prob - prediction.implied_prob
    edge_sign = "+" if edge >= 0 else ""
    edge_note = _edge_interpretation(edge, home.name)
    print(f"  Probabilidad de que GANE {home.name}:")
    print(f"    Según el modelo: {prediction.my_prob:.1%}")
    print(f"    Según el mercado (1/cuota): {prediction.implied_prob:.1%}")
    print(f"    Edge: {edge_sign}{edge * 100:.1f}%  {edge_note}\n")


def _edge_interpretation(edge: float, home_name: str) -> str:
    if edge > 0.005:
        return f"(mercado subestima a {home_name})"
    if edge < -0.005:
        return f"(mercado tiene razón o sobreestima a {home_name})"
    return "(modelo y mercado de acuerdo)"


def _print_money_outcome(prediction, home, away, bankroll, args):
    v = prediction.verdict.verdict
    if v == "esperar":
        print(f"  Edge marginal. Mejor esperar mejor cuota o más info.")
        print(f"  💰 Bankroll: ${bankroll:.2f}")
        return

    payout_if_win = args.stake * args.quota
    profit_if_win = payout_if_win - args.stake
    print(f"  Si apuestas ${args.stake:.0f} a que gana {home.name}:")
    print(f"    ✅ Gana {home.name:<22} → cobras ${payout_if_win:.2f}  (+${profit_if_win:.2f})")
    print(f"    ❌ Empata o gana {away.name[:14]:<14}  → pierdes ${args.stake:.2f}")
    print(f"    📊 EV (esperado a la larga): ${prediction.ev:+.2f}")

    if v == "apostar":
        recommended_stake = prediction.kelly * bankroll if bankroll > 0 else 0
        print(f"\n  💵 Stake recomendado (Kelly): ${recommended_stake:.2f}  de ${bankroll:.2f} bankroll")
        if args.stake > recommended_stake * KELLY_OVERSTAKE_WARNING_MULT:
            print(f"  ⚠️  Vas a apostar más que Kelly — riesgo elevado.")
    else:  # no_apostar
        print(f"  Kelly = 0% (no apostar nada)")


def _print_footer(bar):
    print(f"\n  {bar}")
    print(f"  Detalle técnico: --verbose")
    print(f"  Nota: el modelo solo predice VICTORIA LOCAL (mercado 1X2 → 1).")
    print(f"        Para otros mercados (over/under, BTTS) hace falta otro modelo.\n")


def _short_reasoning(home, away, prediction):
    """One-line summary of why."""
    comp = prediction.reasoning["components"]
    weights = prediction.reasoning["weights"]
    # Find the biggest contributor (signal × weight)
    contributions = {k: comp[k] * weights[k] for k in weights}
    top = max(contributions, key=lambda k: abs(contributions[k]))
    direction = "favorece local" if contributions[top] > 0 else "favorece visitante"
    pretty = {
        "xg_diff": f"diferencia de xG {direction}",
        "shots_diff": f"tiros al arco {direction}",
        "form_diff": f"forma reciente {direction}",
        "goal_diff": f"goles recientes {direction}",
        "possession_diff": f"posesión {direction}",
        "home_advantage": "localía pesa",
        "context": "contexto (importancia/ausencias)",
    }.get(top, top)
    return f"Factor principal: {pretty}"


def _print_verbose(home, away, league, home_features, away_features,
                   prediction, bankroll, args):
    """Full detail output — for debugging or curiosity."""
    print(f"\n{'=' * 70}")
    print(f"PREDICTION: {home.name}  vs  {away.name}")
    print(f"League: {league}  |  Quota: {args.quota}  |  Stake: ${args.stake}")
    print(f"{'=' * 70}\n")

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

    print(f"\n{'=' * 70}")
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

    if bankroll > 0:
        recommended_stake = prediction.kelly * bankroll
        print(f"\n  💰 Bankroll disponible: ${bankroll:.2f}")
        print(f"  💵 Stake recomendado (Kelly): ${recommended_stake:.2f}")
        if recommended_stake > args.stake:
            print(f"     (Vas a apostar ${args.stake:.2f} — menos que Kelly. Conservador, OK.)")
        elif recommended_stake < args.stake:
            print(f"     ⚠️  Vas a apostar ${args.stake:.2f} — MÁS que Kelly. Riesgo elevado.")

    print(f"\nComponent breakdown:")
    for name, value in prediction.reasoning["components"].items():
        weight = prediction.reasoning["weights"][name]
        contribution = value * weight
        print(f"  {name:18s}  signal={value:+.2f}  weight={weight:.2f}  → {contribution:+.3f}")


if __name__ == "__main__":
    sys.exit(main())
