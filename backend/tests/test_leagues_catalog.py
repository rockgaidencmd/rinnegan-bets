"""Tests for the LEAGUES single source of truth + derived consumers.

If any of these break, it usually means someone added a new league but
forgot to update LEAGUES — these tests catch that early.
"""

from core.leagues import LEAGUES, by_sofascore_id, codes_for_model
from core.models.factory import ECUADOR_STYLE_LEAGUES, EUROPE_LEAGUES
from data.fetchers.sofascore import TOURNAMENT_IDS


class TestLeagueCatalog:

    def test_required_leagues_present(self):
        required = {"PL", "PD", "BL1", "SA", "FL1", "CL", "LIB", "EC1"}
        assert required.issubset(LEAGUES.keys())

    def test_each_league_has_unique_sofascore_id(self):
        ids = [info.sofascore_id for info in LEAGUES.values()]
        assert len(ids) == len(set(ids)), "Duplicate SofaScore IDs in LEAGUES"

    def test_each_league_has_unique_code(self):
        # dict keys are already unique, but verify code field matches the key
        for code, info in LEAGUES.items():
            assert info.code == code

    def test_model_family_is_valid(self):
        valid_families = {"europe", "ecuador"}
        for info in LEAGUES.values():
            assert info.model_family in valid_families


class TestDerivedTournamentIds:

    def test_tournament_ids_derived_from_leagues(self):
        """The fetcher dict must match LEAGUES exactly — no drift allowed."""
        expected = {code: info.sofascore_id for code, info in LEAGUES.items()}
        assert TOURNAMENT_IDS == expected

    def test_premier_league_id_is_17(self):
        # Sanity check against a value we know is correct
        assert TOURNAMENT_IDS["PL"] == 17


class TestModelFactoryDerived:

    def test_europe_leagues_derived(self):
        assert "PL" in EUROPE_LEAGUES
        assert "PD" in EUROPE_LEAGUES
        assert "CL" in EUROPE_LEAGUES
        assert "EC1" not in EUROPE_LEAGUES

    def test_ecuador_leagues_derived(self):
        assert "EC1" in ECUADOR_STYLE_LEAGUES
        assert "LIB" in ECUADOR_STYLE_LEAGUES
        assert "PL" not in ECUADOR_STYLE_LEAGUES

    def test_no_league_in_both_families(self):
        assert EUROPE_LEAGUES.isdisjoint(ECUADOR_STYLE_LEAGUES)

    def test_all_leagues_covered(self):
        """Every LEAGUES entry must route to exactly one model family."""
        assert EUROPE_LEAGUES | ECUADOR_STYLE_LEAGUES == set(LEAGUES.keys())


class TestReverseLookup:

    def test_by_sofascore_id_finds_known(self):
        assert by_sofascore_id(17).code == "PL"
        assert by_sofascore_id(240).code == "EC1"

    def test_by_sofascore_id_returns_none_for_unknown(self):
        assert by_sofascore_id(99999) is None


class TestCodesForModel:

    def test_returns_set(self):
        assert isinstance(codes_for_model("europe"), set)

    def test_unknown_family_returns_empty(self):
        assert codes_for_model("nonexistent") == set()
