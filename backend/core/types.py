"""Domain types for the prediction engine.

Type-first: model contracts defined here. Implementations satisfy them.
Pure data — no behavior, no I/O dependencies.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, NewType


# --- Domain primitives (NewType prevents accidental mix-ups) ---

Probability = NewType("Probability", float)   # 0.0 to 1.0
Odds = NewType("Odds", float)                  # > 1.0 (decimal odds)
Stake = NewType("Stake", float)                # currency amount, >= 0
EV = NewType("EV", float)                      # expected value, can be negative
KellyFraction = NewType("KellyFraction", float)  # 0.0 to 1.0 (fraction of bankroll)


def make_probability(value: float) -> Probability:
    """Constructor that validates the range [0, 1]."""
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Probability must be in [0, 1], got {value}")
    return Probability(value)


def make_odds(value: float) -> Odds:
    """Constructor that validates odds > 1 (otherwise no payout above stake)."""
    if value <= 1.0:
        raise ValueError(f"Odds must be > 1.0, got {value}")
    return Odds(value)


# --- Features extracted from historical matches ---

@dataclass(frozen=True)
class TeamFeatures:
    """Features for one team, extracted from recent matches.

    Some fields are nullable when the league doesn't expose them (e.g.,
    Liga Pro Ecuador often lacks xG). Models must handle None gracefully.
    """

    team_id: int
    matches_analyzed: int       # how many games went into these averages

    # Form
    wins: int
    draws: int
    losses: int
    form_score: float           # 0-100 (points per max possible)

    # Offense / Defense — basic
    avg_goals_for: float
    avg_goals_against: float

    # Advanced (None when source API doesn't provide)
    avg_xg_for: float | None = None
    avg_xg_against: float | None = None
    avg_possession: float | None = None
    avg_shots_on_target: float | None = None
    avg_corners: float | None = None


@dataclass(frozen=True)
class MatchContext:
    """User-provided context about a specific upcoming match."""

    importance: Literal["final", "clasif", "normal", "calendario"] = "normal"
    home_key_absences: bool = False
    away_key_absences: bool = False
    # Future: days_rest, weather, h2h, etc.


# --- Prediction output (discriminated union of verdicts) ---

@dataclass(frozen=True)
class Apostar:
    """Recommend placing the bet."""
    verdict: Literal["apostar"] = "apostar"
    reason: str = ""


@dataclass(frozen=True)
class Esperar:
    """Marginal edge — wait for more info or better odds."""
    verdict: Literal["esperar"] = "esperar"
    reason: str = ""


@dataclass(frozen=True)
class NoApostar:
    """No edge or negative edge — skip."""
    verdict: Literal["no_apostar"] = "no_apostar"
    reason: str = ""


Verdict = Apostar | Esperar | NoApostar


@dataclass(frozen=True)
class Prediction:
    """Output of a model evaluation. Pure data, no behavior."""

    model_version: str
    home_team_id: int
    away_team_id: int

    pre_score: float            # 0-100, our model's confidence
    implied_prob: Probability   # market's prob (1/odds)
    my_prob: Probability        # our prob (blended from pre_score + market)

    quota: Odds                 # odds the user is being offered
    stake: Stake                # user's intended stake
    ev: EV                      # expected value of the bet
    kelly: KellyFraction        # recommended bet fraction (cap-applied)

    verdict: Verdict
    reasoning: dict             # which features drove the score (explainability)
