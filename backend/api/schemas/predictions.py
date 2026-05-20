"""Prediction schemas — Request/Response for the predict endpoint."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    """User asks: should I bet on home_team to beat away_team at this quota?"""

    home_team: str = Field(min_length=1, description="Home team name or alias")
    away_team: str = Field(min_length=1, description="Away team name or alias")
    quota: float = Field(gt=1.0, description="Decimal odds offered by bookmaker")
    stake: float = Field(gt=0, description="Amount user intends to stake")
    importance: Literal["final", "clasif", "normal", "calendario"] = "normal"
    home_key_absences: bool = False
    away_key_absences: bool = False
    force: bool = Field(False, description="Force prediction even if teams don't share a league")


class PredictResponse(BaseModel):
    """Full prediction output — used by the frontend to render the verdict screen."""

    # "model_version" would collide with Pydantic's protected `model_` namespace
    model_config = ConfigDict(protected_namespaces=())

    # Identification
    home_team: str
    away_team: str
    league: str
    market: str = "victoria_local"   # currently the only supported market
    model_version: str

    # Probabilities (0-1 floats — frontend formats as %)
    my_prob: float
    implied_prob: float
    edge: float                       # my_prob - implied_prob

    # Money
    quota: float
    stake: float
    ev: float                         # expected value of the bet
    kelly: float                      # 0-1 fraction of bankroll

    # Recommendation
    pre_score: float                  # 0-100
    verdict: Literal["apostar", "esperar", "no_apostar"]
    verdict_reason: str

    # Explainability
    reasoning: dict[str, Any]
