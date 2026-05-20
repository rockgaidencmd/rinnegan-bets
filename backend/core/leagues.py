"""Single source of truth for league metadata.

Anywhere in the codebase that needs to know about a league — its display
name, country, SofaScore id, which model family applies — imports from here.

To add a new league: add ONE entry below. All other places (API responses,
scrapers, model factory, parsers) derive their info from this dict.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LeagueInfo:
    code: str               # Our internal code (matches db.enums.League values)
    name: str               # Human-readable display name
    country: str            # Country or region the league belongs to
    sofascore_id: int       # SofaScore's uniqueTournament.id
    football_data_id: str | None = None  # Football-Data API competition code (None = not available there)
    model_family: str = "europe"         # Which prediction model: "europe" (xG-based) or "ecuador" (proxy-based)


# Single source of truth. Add new leagues here only.
LEAGUES: dict[str, LeagueInfo] = {
    "PL": LeagueInfo(
        code="PL", name="Premier League", country="England",
        sofascore_id=17, football_data_id="PL", model_family="europe",
    ),
    "PD": LeagueInfo(
        code="PD", name="La Liga", country="Spain",
        sofascore_id=8, football_data_id="PD", model_family="europe",
    ),
    "BL1": LeagueInfo(
        code="BL1", name="Bundesliga", country="Germany",
        sofascore_id=35, football_data_id="BL1", model_family="europe",
    ),
    "SA": LeagueInfo(
        code="SA", name="Serie A", country="Italy",
        sofascore_id=23, football_data_id="SA", model_family="europe",
    ),
    "FL1": LeagueInfo(
        code="FL1", name="Ligue 1", country="France",
        sofascore_id=34, football_data_id="FL1", model_family="europe",
    ),
    "CL": LeagueInfo(
        code="CL", name="Champions League", country="Europe",
        sofascore_id=7, football_data_id="CL", model_family="europe",
    ),
    "LIB": LeagueInfo(
        code="LIB", name="Copa Libertadores", country="South America",
        sofascore_id=16940, football_data_id=None, model_family="ecuador",
    ),
    "EC1": LeagueInfo(
        code="EC1", name="LigaPro Ecuador", country="Ecuador",
        sofascore_id=240, football_data_id=None, model_family="ecuador",
    ),
}


# Derived lookup helpers — DO NOT redefine these elsewhere.

def by_sofascore_id(sofa_id: int) -> LeagueInfo | None:
    """Reverse lookup: SofaScore tournament id → our LeagueInfo."""
    for info in LEAGUES.values():
        if info.sofascore_id == sofa_id:
            return info
    return None


def codes_for_model(family: str) -> set[str]:
    """All league codes that use a given model family."""
    return {code for code, info in LEAGUES.items() if info.model_family == family}
