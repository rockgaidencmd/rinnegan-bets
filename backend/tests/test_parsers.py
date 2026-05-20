"""Tests for parsers — uses real API response fixtures captured live.

Fixtures live in tests/fixtures/ and are committed to git so tests
can detect when SofaScore or Football-Data change their response schema.
"""

import json
from pathlib import Path

import pytest

from data.parsers import ParsedTeam
from data.parsers.football_data_parser import parse_competition_teams
from data.parsers.sofascore_parser import parse_season_teams


FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    with open(FIXTURES / name) as f:
        return json.load(f)


# --- SofaScore parser ---

class TestSofaScoreParser:

    def test_parses_ecuador_teams_from_real_fixture(self):
        payload = _load_fixture("sofascore_ecuador_teams.json")
        teams = parse_season_teams(payload, league_code="EC1")

        assert len(teams) == 16
        assert all(isinstance(t, ParsedTeam) for t in teams)

    def test_ecuador_teams_have_required_fields(self):
        payload = _load_fixture("sofascore_ecuador_teams.json")
        teams = parse_season_teams(payload, league_code="EC1")

        for t in teams:
            assert t.name
            assert t.slug
            assert t.league == "EC1"
            assert t.sofascore_id is not None
            # Ecuador teams should have Ecuador country
            assert t.country == "Ecuador"

    def test_returns_empty_list_when_no_teams_key(self):
        assert parse_season_teams({}, "EC1") == []

    def test_returns_empty_list_when_teams_empty(self):
        assert parse_season_teams({"teams": []}, "EC1") == []

    def test_skips_teams_without_id_or_name(self):
        payload = {"teams": [
            {"id": 1, "name": "Valid"},
            {"id": None, "name": "No ID"},
            {"id": 2, "name": ""},  # empty name
            {"id": 3, "name": "Also valid"},
        ]}
        teams = parse_season_teams(payload, "EC1")
        assert len(teams) == 2
        assert {t.name for t in teams} == {"Valid", "Also valid"}

    def test_falls_back_to_generated_slug_when_missing(self):
        payload = {"teams": [{"id": 1, "name": "Real Madrid CF"}]}
        teams = parse_season_teams(payload, "PD")
        assert teams[0].slug == "real-madrid-cf"

    def test_uses_category_country_when_country_field_missing(self):
        payload = {"teams": [{
            "id": 1, "name": "X", "slug": "x",
            "category": {"country": {"name": "Brazil"}},
        }]}
        teams = parse_season_teams(payload, "OTHER")
        assert teams[0].country == "Brazil"


# --- Football-Data parser ---

class TestFootballDataParser:

    def test_parses_premier_league_teams_from_real_fixture(self):
        payload = _load_fixture("football_data_pl_teams.json")
        teams = parse_competition_teams(payload, league_code="PL")

        assert len(teams) == 20
        assert all(isinstance(t, ParsedTeam) for t in teams)

    def test_premier_teams_have_required_fields(self):
        payload = _load_fixture("football_data_pl_teams.json")
        teams = parse_competition_teams(payload, league_code="PL")

        for t in teams:
            assert t.name
            assert t.slug
            assert t.league == "PL"
            assert t.football_data_id is not None
            assert t.country == "England"

    def test_arsenal_specific_fields(self):
        """Spot-check a known team to catch silent regressions."""
        payload = _load_fixture("football_data_pl_teams.json")
        teams = parse_competition_teams(payload, league_code="PL")

        arsenal = next(t for t in teams if "Arsenal" in t.name)
        assert arsenal.football_data_id == 57
        assert arsenal.country == "England"
        assert arsenal.league == "PL"

    def test_slugs_are_url_safe(self):
        payload = _load_fixture("football_data_pl_teams.json")
        teams = parse_competition_teams(payload, league_code="PL")

        for t in teams:
            # No spaces, no special chars except dashes
            assert " " not in t.slug
            assert "'" not in t.slug
            assert "." not in t.slug

    def test_returns_empty_when_no_teams(self):
        assert parse_competition_teams({}, "PL") == []
        assert parse_competition_teams({"teams": []}, "PL") == []

    def test_handles_team_without_short_name(self):
        payload = {"teams": [{
            "id": 1, "name": "FC Bayern München",
            "area": {"name": "Germany"},
        }]}
        teams = parse_competition_teams(payload, "BL1")
        # Falls back to name when shortName missing
        assert "bayern" in teams[0].slug.lower()
