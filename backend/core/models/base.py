"""PredictionModel Protocol — interface all models must satisfy.

Structural typing: a class with these attrs is a PredictionModel.
No inheritance needed — just satisfy the interface.
"""

from typing import Protocol

from core.types import MatchContext, Prediction, TeamFeatures


class PredictionModel(Protocol):
    """Pluggable prediction model. Pure function over features + context + market."""

    version: str
    weights: dict[str, float]

    def predict(
        self,
        home: TeamFeatures,
        away: TeamFeatures,
        context: MatchContext,
        quota: float,
        stake: float,
    ) -> Prediction:
        ...
