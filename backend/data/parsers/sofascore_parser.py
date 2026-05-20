"""Parse SofaScore JSON responses into normalized internal types."""

from data.parsers import ParsedTeam


def parse_season_teams(payload: dict, league_code: str) -> list[ParsedTeam]:
    """Convert SofaScore season teams response to ParsedTeam list.

    Expected payload shape:
        {"teams": [
            {"id": 123, "name": "Barcelona SC", "slug": "barcelona-sc",
             "country": {"name": "Ecuador"}}, ...]}

    Args:
        payload: Raw JSON dict from SofaScoreFetcher.get_season_teams()
        league_code: Internal league code (e.g., "EC1", "PL")

    Returns:
        List of ParsedTeam — empty list if no teams in payload.
    """
    teams_raw = payload.get("teams", [])
    parsed: list[ParsedTeam] = []

    for team in teams_raw:
        if not _is_valid_team(team):
            continue

        parsed.append(ParsedTeam(
            name=team["name"],
            slug=team.get("slug") or _slugify(team["name"]),
            league=league_code,
            country=_extract_country(team),
            sofascore_id=team["id"],
        ))

    return parsed


def _is_valid_team(team: dict) -> bool:
    """Skip entries without minimum required fields."""
    return bool(team.get("id") and team.get("name"))


def _extract_country(team: dict) -> str | None:
    """SofaScore puts country under team.country.name or team.category.country.name."""
    country = team.get("country", {})
    if country.get("name"):
        return country["name"]
    category_country = team.get("category", {}).get("country", {})
    return category_country.get("name")


def _slugify(name: str) -> str:
    """Fallback slug generator when SofaScore doesn't provide one."""
    return name.lower().replace(" ", "-").replace(".", "")
