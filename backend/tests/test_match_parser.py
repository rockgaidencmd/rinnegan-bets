"""Tests for SofaScore match parser using real captured fixtures."""

import json
from datetime import timezone
from pathlib import Path

import pytest

from data.parsers import ParsedMatch
from data.parsers.sofascore_match_parser import (
    merge_statistics,
    parse_team_events,
    _parse_float,
    _parse_int,
    _parse_percentage,
)


FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    with open(FIXTURES / name) as f:
        return json.load(f)


class TestParseTeamEvents:

    def test_parses_finished_events_only(self):
        payload = _load("sofascore_team_events.json")
        matches = parse_team_events(payload, league_code="EC1")

        # All should be finished
        assert all(m.status == "finished" for m in matches)
        # All should have goals set
        assert all(m.home_goals is not None and m.away_goals is not None for m in matches)

    def test_first_match_has_required_fields(self):
        payload = _load("sofascore_team_events.json")
        matches = parse_team_events(payload, league_code="EC1")

        assert len(matches) > 0
        m = matches[0]
        assert isinstance(m, ParsedMatch)
        assert m.external_id
        assert m.source == "sofascore"
        assert m.league == "EC1"
        assert m.home_team_sofascore_id > 0
        assert m.away_team_sofascore_id > 0
        assert m.home_team_name
        assert m.away_team_name
        assert m.match_date.tzinfo == timezone.utc

    def test_result_computed_from_goals(self):
        payload = _load("sofascore_team_events.json")
        matches = parse_team_events(payload, league_code="EC1")

        for m in matches:
            if m.home_goals > m.away_goals:
                assert m.result == "H"
            elif m.home_goals < m.away_goals:
                assert m.result == "A"
            else:
                assert m.result == "D"

    def test_skips_non_finished_events(self):
        payload = {"events": [
            {"id": 1, "status": {"type": "notstarted"},
             "homeTeam": {"id": 1, "name": "X"}, "awayTeam": {"id": 2, "name": "Y"},
             "startTimestamp": 1000, "homeScore": {}, "awayScore": {}},
            {"id": 2, "status": {"type": "finished"},
             "homeTeam": {"id": 1, "name": "X"}, "awayTeam": {"id": 2, "name": "Y"},
             "startTimestamp": 1000,
             "homeScore": {"current": 1}, "awayScore": {"current": 0}},
        ]}
        matches = parse_team_events(payload, "PL")
        assert len(matches) == 1
        assert matches[0].external_id == "2"

    def test_returns_empty_for_empty_payload(self):
        assert parse_team_events({}, "PL") == []
        assert parse_team_events({"events": []}, "PL") == []


class TestMergeStatistics:

    def test_merges_xg_from_real_fixture(self):
        events = _load("sofascore_team_events.json")
        stats = _load("sofascore_event_statistics.json")

        match = parse_team_events(events, "LIB")[0]
        # First event in fixture should match the stats event
        enriched = merge_statistics(match, stats)

        # We captured Atlético Mineiro vs IDV — xG was 2.12 / 0.84
        assert enriched.home_xg == 2.12
        assert enriched.away_xg == 0.84

    def test_merges_possession_from_real_fixture(self):
        events = _load("sofascore_team_events.json")
        stats = _load("sofascore_event_statistics.json")

        match = parse_team_events(events, "LIB")[0]
        enriched = merge_statistics(match, stats)

        # Real values: 46% / 54%
        assert enriched.home_possession == 46.0
        assert enriched.away_possession == 54.0

    def test_merges_corners_from_real_fixture(self):
        events = _load("sofascore_team_events.json")
        stats = _load("sofascore_event_statistics.json")

        match = parse_team_events(events, "LIB")[0]
        enriched = merge_statistics(match, stats)

        # Real values: 4 / 5
        assert enriched.home_corners == 4
        assert enriched.away_corners == 5

    def test_merges_shots_on_target_from_real_fixture(self):
        events = _load("sofascore_team_events.json")
        stats = _load("sofascore_event_statistics.json")

        match = parse_team_events(events, "LIB")[0]
        enriched = merge_statistics(match, stats)

        # Real values: 7 / 4
        assert enriched.home_shots_on_target == 7
        assert enriched.away_shots_on_target == 4

    def test_handles_missing_stats_gracefully(self):
        events = _load("sofascore_team_events.json")
        match = parse_team_events(events, "EC1")[0]

        # Empty stats payload
        enriched = merge_statistics(match, {})
        assert enriched.home_xg is None
        assert enriched.away_xg is None
        # Original fields preserved
        assert enriched.external_id == match.external_id

    def test_does_not_mutate_original(self):
        events = _load("sofascore_team_events.json")
        stats = _load("sofascore_event_statistics.json")

        match = parse_team_events(events, "EC1")[0]
        original_xg = match.home_xg
        enriched = merge_statistics(match, stats)

        # Original ParsedMatch is frozen, must not have been mutated
        assert match.home_xg == original_xg
        assert enriched.home_xg != match.home_xg or original_xg is not None


class TestHelpers:

    def test_parse_float_handles_strings(self):
        assert _parse_float("1.5") == 1.5
        assert _parse_float("2") == 2.0
        assert _parse_float(None) is None
        assert _parse_float("") is None
        assert _parse_float("bad") is None

    def test_parse_int_handles_slash_format(self):
        # SofaScore sometimes gives '7/12' for accuracy stats
        assert _parse_int("7/12") == 7
        assert _parse_int("5") == 5
        assert _parse_int(3) == 3
        assert _parse_int(None) is None

    def test_parse_percentage_strips_percent_sign(self):
        assert _parse_percentage("46%") == 46.0
        assert _parse_percentage("100%") == 100.0
        assert _parse_percentage(46) == 46.0
        assert _parse_percentage(None) is None
