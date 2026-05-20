"""Ecuador model — Liga Pro Serie A.

SofaScore exposes basic stats (possession, shots, corners) but xG is
sparse/missing. This model uses shots-on-target + possession as proxies
for offensive quality.

Home advantage weighted higher: Ecuadorian league has stronger localía
(altitude in Quito teams, etc.).
"""

from dataclasses import dataclass

from core.bankroll.kelly import compute_ev, kelly_fraction, verdict_from_ev_kelly
from core.models.europe import (
    _context_signal,
    _normalize_diff,
    components_summary,
)
from core.types import (
    EV,
    MatchContext,
    Prediction,
    Stake,
    TeamFeatures,
    make_odds,
    make_probability,
)


ECUADOR_WEIGHTS = {
    "shots_diff": 0.25,         # Substitute for xG
    "form_diff": 0.20,          # Recent results
    "goal_diff": 0.15,
    "possession_diff": 0.15,
    "home_advantage": 0.20,     # Stronger than Europe (altitude, crowd, travel)
    "context": 0.05,            # Less data — weight less
}


@dataclass(frozen=True)
class EcuadorModel:
    """Pure-function prediction model for Liga Pro Ecuador."""

    version: str = "ecuador_v1"
    weights: dict[str, float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.weights is None:
            object.__setattr__(self, "weights", ECUADOR_WEIGHTS)
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


def _compute_components(
    home: TeamFeatures, away: TeamFeatures, context: MatchContext
) -> dict[str, float]:
    """Like Europe but uses shots_on_target as xG proxy."""
    return {
        "shots_diff": _normalize_diff(
            home.avg_shots_on_target or 3.0,
            away.avg_shots_on_target or 3.0,
            scale=4.0,
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
        "home_advantage": 0.6,  # Stronger than Europe's 0.5
        "context": _context_signal(context),
    }


def _blend(components: dict[str, float], weights: dict[str, float]) -> float:
    weighted_sum = sum(components[k] * weights[k] for k in weights)
    return max(0.0, min(100.0, 50.0 + weighted_sum * 50.0))


def _blend_probabilities(pre_score, implied):
    from core.types import make_probability
    model_prob = pre_score / 100.0
    blended = 0.4 * model_prob + 0.6 * implied
    return make_probability(min(0.95, max(0.05, blended)))
