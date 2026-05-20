"""Team search with aliases + matchup resolution.

Used by scripts and (eventually) the FastAPI layer to translate user-friendly
team names (including nicknames) into actual DB rows, and to validate
that two teams could legitimately play each other.
"""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from db.models import Team


# Leagues where teams from different domestic leagues can legitimately meet
INTERNATIONAL_LEAGUES = {"CL", "LIB"}


# Common nicknames → official substring stored in DB.
# Case-insensitive lookup. Add new ones as users hit "not found".
TEAM_ALIASES = {
    # Ecuador
    "idv": "Independiente del Valle",
    "bsc": "Barcelona SC",
    "u. católica": "Universidad Católica del Ecuador",
    "u catolica": "Universidad Católica del Ecuador",
    # Europa
    "manu": "Manchester United",
    "man utd": "Manchester United",
    "man united": "Manchester United",
    "mancity": "Manchester City",
    "man city": "Manchester City",
    "psg": "Paris Saint-Germain",
    "atleti": "Atlético de Madrid",
    "spurs": "Tottenham",
    "barça": "FC Barcelona",
    "barca": "FC Barcelona",
    "bayern": "Bayern München",
    "dortmund": "Borussia Dortmund",
    "bvb": "Borussia Dortmund",
}


class TeamSearchError(Exception):
    """Raised when team name lookup or matchup resolution fails."""


def _suggest_similar(session: Session, name: str, limit: int = 5) -> list[str]:
    """Find teams whose name contains any word ≥3 chars from input."""
    words = [w for w in name.split() if len(w) >= 3]
    if not words:
        return []
    conditions = [Team.name.ilike(f"%{w}%") for w in words]
    return list(session.execute(
        select(Team.name).where(or_(*conditions)).distinct().limit(limit)
    ).scalars().all())


def find_teams_by_name(session: Session, name: str) -> list[Team]:
    """Return all Team rows matching name. Resolves aliases automatically.

    Raises TeamSearchError with suggestions if nothing matches.
    A single name can match multiple rows (e.g. Real Madrid in PD + CL).
    """
    lookup = TEAM_ALIASES.get(name.lower().strip(), name)
    teams = session.execute(
        select(Team).where(Team.name.ilike(f"%{lookup}%"))
    ).scalars().all()

    if not teams:
        suggestions = _suggest_similar(session, name)
        hint = ""
        if suggestions:
            hint = "\n   Sugerencias: " + ", ".join(f'"{s}"' for s in suggestions[:3])
        raise TeamSearchError(
            f"Team not found: '{name}'.{hint}\n"
            f"   Aliases conocidos: {', '.join(sorted(TEAM_ALIASES.keys()))}"
        )
    return teams


def resolve_matchup(
    home_candidates: list[Team], away_candidates: list[Team], force: bool = False,
) -> tuple[Team, Team, str]:
    """Pick the right (home, away, league) tuple for a realistic matchup.

    Logic:
      1. Both teams in same domestic league → use it.
      2. Only in same international league (CL/LIB) → use that.
      3. No shared league → reject (unless force=True).
    """
    home_leagues = {t.league for t in home_candidates}
    away_leagues = {t.league for t in away_candidates}
    shared = home_leagues & away_leagues
    domestic_shared = shared - INTERNATIONAL_LEAGUES

    if domestic_shared:
        league = sorted(domestic_shared)[0]
    elif shared:
        league = sorted(shared)[0]
    elif force:
        league = sorted(home_leagues)[0]
        home = next(t for t in home_candidates if t.league == league)
        away = away_candidates[0]
        return home, away, league
    else:
        raise TeamSearchError(
            f"'{home_candidates[0].name}' ({sorted(home_leagues)}) "
            f"y '{away_candidates[0].name}' ({sorted(away_leagues)}) "
            f"no comparten liga. Estos equipos no jugarían entre sí.\n"
            f"   Usa --force para predecir igual (escenario hipotético)."
        )

    home = next(t for t in home_candidates if t.league == league)
    away = next(t for t in away_candidates if t.league == league)
    return home, away, league
