"""Tests for SofaScore match parser using real captured fixtures."""

import json
from datetime import datetime, timezone
from pathlib import Path

from data.parsers import ParsedMatch
from data.parsers.sofascore_match_parser import (
    SOFASCORE_TOURNAMENT_TO_LEAGUE,
    merge_statistics,
    parse_team_performance,
    _parse_float,
    _parse_int,
    _parse_percentage,
)


FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    with open(FIXTURES / name) as f:
        return json.load(f)


def _make_match(**overrides) -> ParsedMatch:
    """Build a ParsedMatch with sensible defaults for stat-merge tests."""
    defaults = dict(
        external_id="x", source="sofascore", league="EC1",
        home_team_sofascore_id=1, away_team_sofascore_id=2,
        home_team_name="A", away_team_name="B",
        match_date=datetime.now(timezone.utc), status="finished",
        home_goals=3, away_goals=1, result="H",
    )
    defaults.update(overrides)
    return ParsedMatch(**defaults)


class TestParseTeamPerformance:

    def test_parses_finished_events_from_real_fixture(self):
        matches = parse_team_performance(_load("sofascore_team_performance.json"))
        assert len(matches) > 0
        assert all(m.status == "finished" for m in matches)

    def test_assigns_league_per_match_from_tournament_id(self):
        """Each match's league comes from tournament.uniqueTournament.id."""
        matches = parse_team_performance(_load("sofascore_team_performance.json"))
        # All matches in this fixture are Emelec → Liga Pro Ecuador
        assert all(m.league == "EC1" for m in matches)

    def test_skips_untracked_tournaments(self):
        """Friendlies / Copa Ecuador / U19 are filtered out."""
        payload = {"events": [
            {
                "id": 1, "status": {"type": "finished"},
                "tournament": {"uniqueTournament": {"id": 99999}},  # untracked
                "homeTeam": {"id": 1, "name": "X"}, "awayTeam": {"id": 2, "name": "Y"},
                "startTimestamp": 1700000000,
                "homeScore": {"current": 1}, "awayScore": {"current": 0},
            },
            {
                "id": 2, "status": {"type": "finished"},
                "tournament": {"uniqueTournament": {"id": 17}},  # PL
                "homeTeam": {"id": 3, "name": "A"}, "awayTeam": {"id": 4, "name": "B"},
                "startTimestamp": 1700000000,
                "homeScore": {"current": 2}, "awayScore": {"current": 1},
            },
        ]}
        matches = parse_team_performance(payload)
        assert len(matches) == 1
        assert matches[0].external_id == "2"
        assert matches[0].league == "PL"

    def test_skips_non_finished_events(self):
        payload = {"events": [{
            "id": 1, "status": {"type": "notstarted"},
            "tournament": {"uniqueTournament": {"id": 17}},
            "homeTeam": {"id": 1, "name": "X"}, "awayTeam": {"id": 2, "name": "Y"},
            "startTimestamp": 1700000000,
            "homeScore": {}, "awayScore": {},
        }]}
        assert parse_team_performance(payload) == []

    def test_returns_empty_for_empty_payload(self):
        assert parse_team_performance({}) == []
        assert parse_team_performance({"events": []}) == []

    def test_result_computed_from_goals(self):
        matches = parse_team_performance(_load("sofascore_team_performance.json"))
        for m in matches:
            if m.home_goals > m.away_goals:
                assert m.result == "H"
            elif m.home_goals < m.away_goals:
                assert m.result == "A"
            else:
                assert m.result == "D"

    def test_match_date_is_utc_aware(self):
        matches = parse_team_performance(_load("sofascore_team_performance.json"))
        assert matches[0].match_date.tzinfo == timezone.utc


class TestMergeStatistics:

    def test_merges_xg_from_real_fixture(self):
        stats = _load("sofascore_event_statistics.json")
        enriched = merge_statistics(_make_match(), stats)
        # Real values from the captured fixture: 2.12 / 0.84
        assert enriched.home_xg == 2.12
        assert enriched.away_xg == 0.84

    def test_merges_possession_corners_shots(self):
        stats = _load("sofascore_event_statistics.json")
        enriched = merge_statistics(_make_match(), stats)
        assert enriched.home_possession == 46.0
        assert enriched.away_possession == 54.0
        assert enriched.home_corners == 4
        assert enriched.away_corners == 5
        assert enriched.home_shots_on_target == 7

    def test_handles_missing_stats_gracefully(self):
        enriched = merge_statistics(_make_match(external_id="x"), {})
        assert enriched.home_xg is None
        assert enriched.external_id == "x"

    def test_does_not_mutate_original(self):
        stats = _load("sofascore_event_statistics.json")
        original = _make_match()
        enriched = merge_statistics(original, stats)
        # Frozen dataclass — replace returns a new instance
        assert original.home_xg is None
        assert enriched.home_xg is not None


class TestHelpers:

    def test_parse_float_handles_strings(self):
        assert _parse_float("1.5") == 1.5
        assert _parse_float(None) is None
        assert _parse_float("") is None
        assert _parse_float("bad") is None

    def test_parse_int_handles_slash_format(self):
        # SofaScore sometimes returns '7/12' for accuracy stats
        assert _parse_int("7/12") == 7
        assert _parse_int("5") == 5
        assert _parse_int(None) is None

    def test_parse_percentage_strips_percent_sign(self):
        assert _parse_percentage("46%") == 46.0
        assert _parse_percentage(46) == 46.0
        assert _parse_percentage(None) is None


class TestTournamentMapping:

    def test_mapping_includes_canonical_leagues(self):
        assert SOFASCORE_TOURNAMENT_TO_LEAGUE[17] == "PL"
        assert SOFASCORE_TOURNAMENT_TO_LEAGUE[240] == "EC1"

    def test_no_duplicate_tournament_ids(self):
        values = list(SOFASCORE_TOURNAMENT_TO_LEAGUE.values())
        assert len(values) == len(set(values))
