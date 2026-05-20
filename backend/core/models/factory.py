"""Model selector: returns the right PredictionModel for a given league.

Which model fits which league is declared in core/leagues.py (model_family).
This file only maps family → model instance.
"""

from core.leagues import LEAGUES, codes_for_model
from core.models.base import PredictionModel
from core.models.ecuador import EcuadorModel
from core.models.europe import EuropeModel


# Derived: which league codes route to which model family.
EUROPE_LEAGUES = codes_for_model("europe")
ECUADOR_STYLE_LEAGUES = codes_for_model("ecuador")


def get_model_for_league(league: str) -> PredictionModel:
    """Return the appropriate model for a league.

    Raises ValueError for unsupported leagues — explicit failure beats
    silently defaulting to a model that may not fit.
    """
    info = LEAGUES.get(league)
    if info is None:
        raise ValueError(
            f"No model configured for league '{league}'. "
            f"Supported: {sorted(LEAGUES.keys())}"
        )
    if info.model_family == "europe":
        return EuropeModel()
    if info.model_family == "ecuador":
        return EcuadorModel()
    raise ValueError(f"Unknown model family '{info.model_family}' for league '{league}'")
