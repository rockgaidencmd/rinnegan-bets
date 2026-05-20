"""Europe model — uses xG/xA, form, market edge.

For Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Champions League.
Requires xG data (which SofaScore provides for these leagues).
"""

from dataclasses import dataclass

from core.bankroll.kelly import compute_ev, kelly_fraction, verdict_from_ev_kelly
from core.types import (
    EV,
    KellyFraction,
    MatchContext,
    Odds,
    Prediction,
    Probability,
    Stake,
    TeamFeatures,
    make_odds,
    make_probability,
)


# Weights tuned on intuition + literature. Sum must equal 1.0.
# These get validated by backtesting in Phase 8.
EUROPE_WEIGHTS = {
    "xg_diff": 0.30,            # Quality of chances
    "form_diff": 0.20,          # Recent results
    "goal_diff": 0.15,          # Actual goals (less reliable than xG but real)
    "possession_diff": 0.10,    # Control of game
    "home_advantage": 0.15,     # Baseline edge for playing at home
    "context": 0.10,            # Importance, absences
}

IMPORTANCE_MULTIPLIER = {
    "final": 1.0,
    "clasif": 0.5,
    "normal": 0.0,
    "calendario": -0.5,
}


@dataclass(frozen=True)
class EuropeModel:
    """Pure-function prediction model for European leagues."""

    version: str = "europe_v1"
    weights: dict[str, float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # Inject default weights without mutating frozen dataclass
        if self.weights is None:
            object.__setattr__(self, "weights", EUROPE_WEIGHTS)
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    def predict(
        self,
        home: TeamFeatures,
        away: TeamFeatures,
        context: MatchContext,
        quota: float,
        stake: float,
    ) -> Prediction:
        odds = make_odds(quota)
        components = _compute_components(home, away, context)
        pre_score = _blend(components, self.weights)

        implied = make_probability(1.0 / odds)
        my_prob = _blend_probabilities(pre_score, implied)

        ev = compute_ev(my_prob, odds, Stake(stake))
        kelly = kelly_fraction(my_prob, odds)
        verdict = verdict_from_ev_kelly(ev, kelly, components_summary(home, away))

        return Prediction(
            model_version=self.version,
            home_team_id=home.team_id,
            away_team_id=away.team_id,
            pre_score=pre_score,
            implied_prob=implied,
            my_prob=my_prob,
            quota=odds,
            stake=Stake(stake),
            ev=ev,
            kelly=kelly,
            verdict=verdict,
            reasoning={
                "components": components,
                "weights": dict(self.weights),
            },
        )


# --- private helpers (pure functions) ---

def _compute_components(
    home: TeamFeatures, away: TeamFeatures, context: MatchContext
) -> dict[str, float]:
    """Each component returns a value in [-1, +1] favoring home (+) or away (-)."""
    return {
        "xg_diff": _normalize_diff(
            (home.avg_xg_for or 0) - (home.avg_xg_against or 0),
            (away.avg_xg_for or 0) - (away.avg_xg_against or 0),
            scale=2.0,  # an xG diff of 2 maxes out the signal
        ),
        "form_diff": _normalize_diff(home.form_score, away.form_score, scale=100.0),
        "goal_diff": _normalize_diff(
            home.avg_goals_for - home.avg_goals_against,
            away.avg_goals_for - away.avg_goals_against,
            scale=2.0,
        ),
        "possession_diff": _normalize_diff(
            home.avg_possession or 50.0, away.avg_possession or 50.0, scale=20.0,
        ),
        "home_advantage": 0.5,  # constant — home teams win ~46% historically
        "context": _context_signal(context),
    }


def _normalize_diff(home_val: float, away_val: float, scale: float) -> float:
    """Convert raw diff to a [-1, +1] signal. scale = saturation point."""
    diff = home_val - away_val
    return max(-1.0, min(1.0, diff / scale))


def _context_signal(context: MatchContext) -> float:
    """Importance bonus + absence penalty. Range [-1, +1]."""
    importance_signal = IMPORTANCE_MULTIPLIER.get(context.importance, 0.0)
    absence_signal = 0.0
    if context.home_key_absences:
        absence_signal -= 0.5
    if context.away_key_absences:
        absence_signal += 0.5
    return max(-1.0, min(1.0, importance_signal * 0.5 + absence_signal))


def _blend(components: dict[str, float], weights: dict[str, float]) -> float:
    """Combine [-1, +1] signals into 0-100 pre_score using weights.

    A weighted average of +1 → 100, of 0 → 50, of -1 → 0.
    """
    weighted_sum = sum(components[k] * weights[k] for k in weights)
    return max(0.0, min(100.0, 50.0 + weighted_sum * 50.0))


def _blend_probabilities(pre_score: float, implied: Probability) -> Probability:
    """Blend our model with the market — neither alone is perfect.

    Our edge = how much our prob differs from market's. We weight 40%
    model, 60% market because the market is informed (many traders).
    """
    model_prob = pre_score / 100.0
    blended = 0.4 * model_prob + 0.6 * implied
    return make_probability(min(0.95, max(0.05, blended)))


def components_summary(home: TeamFeatures, away: TeamFeatures) -> str:
    """Human-readable summary of the inputs (for the verdict reason)."""
    parts = [f"form {home.form_score:.0f} vs {away.form_score:.0f}"]
    if home.avg_xg_for and away.avg_xg_for:
        parts.append(f"xG {home.avg_xg_for:.1f} vs {away.avg_xg_for:.1f}")
    return ", ".join(parts)
