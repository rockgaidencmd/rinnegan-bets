"""Model selector: returns the right PredictionModel for a given league."""

from core.models.base import PredictionModel
from core.models.ecuador import EcuadorModel
from core.models.europe import EuropeModel


# Leagues that have reliable xG data (use Europe model)
EUROPE_LEAGUES = {"PL", "PD", "BL1", "SA", "FL1", "CL"}

# Leagues without consistent xG (use Ecuador-style model)
ECUADOR_STYLE_LEAGUES = {"EC1", "LIB"}


def get_model_for_league(league: str) -> PredictionModel:
    """Return the appropriate model for a league.

    Raises ValueError for unsupported leagues — explicit failure beats
    silently defaulting to a model that may not fit.
    """
    if league in EUROPE_LEAGUES:
        return EuropeModel()
    if league in ECUADOR_STYLE_LEAGUES:
        return EcuadorModel()
    raise ValueError(
        f"No model configured for league '{league}'. "
        f"Supported: {sorted(EUROPE_LEAGUES | ECUADOR_STYLE_LEAGUES)}"
    )
