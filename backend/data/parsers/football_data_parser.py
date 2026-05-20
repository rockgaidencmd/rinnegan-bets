"""Parse Football-Data.org responses into normalized internal types."""

from data.parsers import ParsedTeam


def parse_competition_teams(payload: dict, league_code: str) -> list[ParsedTeam]:
    """Convert Football-Data /competitions/{code}/teams response.

    Expected payload shape:
        {"teams": [
            {"id": 57, "name": "Arsenal FC", "tla": "ARS",
             "shortName": "Arsenal", "area": {"name": "England"}}, ...]}

    Args:
        payload: Raw JSON dict from FootballDataFetcher.get_competition_teams()
        league_code: Internal league code matching League enum (e.g., "PL")

    Returns:
        List of ParsedTeam.
    """
    teams_raw = payload.get("teams", [])
    parsed: list[ParsedTeam] = []

    for team in teams_raw:
        if not _is_valid_team(team):
            continue

        parsed.append(ParsedTeam(
            name=team["name"],
            slug=_slugify(team.get("shortName") or team["name"]),
            league=league_code,
            country=team.get("area", {}).get("name"),
            football_data_id=team["id"],
        ))

    return parsed


def _is_valid_team(team: dict) -> bool:
    return bool(team.get("id") and team.get("name"))


def _slugify(name: str) -> str:
    """Slug for cross-API matching. Lowercase, dashes, no special chars."""
    return (
        name.lower()
        .replace(" ", "-")
        .replace(".", "")
        .replace("'", "")
        .replace("&", "and")
    )
