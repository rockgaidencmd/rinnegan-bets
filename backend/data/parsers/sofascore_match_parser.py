"""Parse SofaScore match-level data (events + statistics)."""

from dataclasses import replace
from datetime import datetime, timezone

from data.fetchers.sofascore import TOURNAMENT_IDS
from data.parsers import ParsedMatch


# Inverse of TOURNAMENT_IDS — derived, not hardcoded.
# Add new leagues in ONE place: data/fetchers/sofascore.py::TOURNAMENT_IDS.
SOFASCORE_TOURNAMENT_TO_LEAGUE = {v: k for k, v in TOURNAMENT_IDS.items()}


def parse_team_performance(payload: dict) -> list[ParsedMatch]:
    """Parse the /team/{id}/performance response.

    Unlike parse_team_events, this resolves league PER MATCH from
    tournament.uniqueTournament.id rather than receiving a single league
    code (the team plays in multiple competitions — Liga + Cup + Champions).

    Matches in tournaments we don't track (FA Cup, Copa Ecuador, friendlies)
    are skipped — not included in the returned list.
    """
    events = payload.get("events", [])
    parsed: list[ParsedMatch] = []

    for event in events:
        status = event.get("status", {}).get("type")
        if status != "finished":
            continue
        if not _is_valid_event(event):
            continue

        tournament_id = (
            event.get("tournament", {})
            .get("uniqueTournament", {})
            .get("id")
        )
        league_code = SOFASCORE_TOURNAMENT_TO_LEAGUE.get(tournament_id)
        if league_code is None:
            # Untracked competition — skip (don't pollute BD with friendlies/etc)
            continue

        home_goals = event.get("homeScore", {}).get("current")
        away_goals = event.get("awayScore", {}).get("current")

        parsed.append(ParsedMatch(
            external_id=str(event["id"]),
            source="sofascore",
            league=league_code,
            home_team_sofascore_id=event["homeTeam"]["id"],
            away_team_sofascore_id=event["awayTeam"]["id"],
            home_team_name=event["homeTeam"]["name"],
            away_team_name=event["awayTeam"]["name"],
            match_date=datetime.fromtimestamp(event["startTimestamp"], tz=timezone.utc),
            status=status,
            home_goals=home_goals,
            away_goals=away_goals,
            result=_compute_result(home_goals, away_goals),
        ))

    return parsed


def parse_team_events(payload: dict, league_code: str) -> list[ParsedMatch]:
    """Convert SofaScore team events response to ParsedMatch list (no stats yet).

    Only includes finished matches (we want results we can validate).
    """
    events = payload.get("events", [])
    parsed: list[ParsedMatch] = []

    for event in events:
        status = event.get("status", {}).get("type")
        if status != "finished":
            continue

        if not _is_valid_event(event):
            continue

        home_goals = event.get("homeScore", {}).get("current")
        away_goals = event.get("awayScore", {}).get("current")

        parsed.append(ParsedMatch(
            external_id=str(event["id"]),
            source="sofascore",
            league=league_code,
            home_team_sofascore_id=event["homeTeam"]["id"],
            away_team_sofascore_id=event["awayTeam"]["id"],
            home_team_name=event["homeTeam"]["name"],
            away_team_name=event["awayTeam"]["name"],
            match_date=datetime.fromtimestamp(
                event["startTimestamp"], tz=timezone.utc
            ),
            status=status,
            home_goals=home_goals,
            away_goals=away_goals,
            result=_compute_result(home_goals, away_goals),
        ))

    return parsed


def merge_statistics(match: ParsedMatch, stats_payload: dict) -> ParsedMatch:
    """Merge an event's statistics payload into an existing ParsedMatch.

    Returns a new ParsedMatch with stat fields populated where extractable.
    Missing stats remain None — model must handle gracefully.
    """
    all_period = _find_all_period(stats_payload)
    if not all_period:
        return match

    stat_map = _flatten_stats(all_period)

    return replace(
        match,
        home_xg=_parse_float(stat_map.get("Expected goals", {}).get("home")),
        away_xg=_parse_float(stat_map.get("Expected goals", {}).get("away")),
        home_possession=_parse_percentage(stat_map.get("Ball possession", {}).get("home")),
        away_possession=_parse_percentage(stat_map.get("Ball possession", {}).get("away")),
        home_shots_on_target=_parse_int(stat_map.get("Shots on target", {}).get("home")),
        away_shots_on_target=_parse_int(stat_map.get("Shots on target", {}).get("away")),
        home_corners=_parse_int(stat_map.get("Corner kicks", {}).get("home")),
        away_corners=_parse_int(stat_map.get("Corner kicks", {}).get("away")),
        home_yellow_cards=_parse_int(stat_map.get("Yellow cards", {}).get("home")),
        away_yellow_cards=_parse_int(stat_map.get("Yellow cards", {}).get("away")),
    )


# --- helpers ---

def _is_valid_event(event: dict) -> bool:
    return bool(
        event.get("id")
        and event.get("homeTeam", {}).get("id")
        and event.get("awayTeam", {}).get("id")
        and event.get("startTimestamp")
    )


def _compute_result(home: int | None, away: int | None) -> str | None:
    if home is None or away is None:
        return None
    if home > away:
        return "H"
    if home < away:
        return "A"
    return "D"


def _find_all_period(stats_payload: dict) -> dict | None:
    """SofaScore returns stats per period ('ALL', '1ST', '2ND'). We want ALL."""
    for period in stats_payload.get("statistics", []):
        if period.get("period") == "ALL":
            return period
    return None


def _flatten_stats(period_block: dict) -> dict[str, dict]:
    """Flatten nested groups into {stat_name: {home, away}} for easy lookup."""
    result = {}
    for group in period_block.get("groups", []):
        for item in group.get("statisticsItems", []):
            name = item.get("name")
            if not name:
                continue
            result[name] = {"home": item.get("home"), "away": item.get("away")}
    return result


def _parse_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


def _parse_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        # Handle '7/12' format — take first number
        s = str(value).split("/")[0].strip()
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _parse_percentage(value) -> float | None:
    """'46%' → 46.0 ; 46 → 46.0 ; None → None."""
    if value is None or value == "":
        return None
    s = str(value).replace("%", "").strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return None
