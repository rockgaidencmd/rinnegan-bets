"""Tests for team search + matchup resolution."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from data.team_search import (
    TEAM_ALIASES,
    TeamSearchError,
    find_teams_by_name,
    resolve_matchup,
)
from db.base import Base
from db.enums import League
from db.models import Team


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _fk(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()
        engine.dispose()


def _seed_teams(session):
    teams = [
        Team(name="Independiente del Valle", slug="independiente-del-valle",
             league=League.LIGA_PRO_ECUADOR.value, country="Ecuador"),
        Team(name="LDU", slug="ldu", league=League.LIGA_PRO_ECUADOR.value, country="Ecuador"),
        Team(name="Barcelona SC Guayaquil", slug="barcelona-sc",
             league=League.LIGA_PRO_ECUADOR.value, country="Ecuador"),
        Team(name="Manchester United FC", slug="manchester-united",
             league=League.PREMIER_LEAGUE.value, country="England"),
        Team(name="FC Bayern München", slug="bayern", league=League.BUNDESLIGA.value, country="Germany"),
        # Same team in two leagues (domestic + international)
        Team(name="Real Madrid CF", slug="real-madrid-cf-pd",
             league=League.LA_LIGA.value, country="Spain"),
        Team(name="Real Madrid CF", slug="real-madrid-cf-cl",
             league=League.CHAMPIONS_LEAGUE.value, country="Spain"),
        Team(name="Liverpool FC", slug="liverpool-fc-pl",
             league=League.PREMIER_LEAGUE.value, country="England"),
        Team(name="Liverpool FC", slug="liverpool-fc-cl",
             league=League.CHAMPIONS_LEAGUE.value, country="England"),
    ]
    session.add_all(teams)
    session.commit()
    return teams


# --- find_teams_by_name ---

class TestFindTeamsByName:

    def test_exact_name_match(self, session):
        _seed_teams(session)
        result = find_teams_by_name(session, "LDU")
        assert len(result) == 1
        assert result[0].name == "LDU"

    def test_substring_match(self, session):
        _seed_teams(session)
        result = find_teams_by_name(session, "Bayern")
        assert any("Bayern" in t.name for t in result)

    def test_alias_idv(self, session):
        _seed_teams(session)
        result = find_teams_by_name(session, "IDV")
        assert result[0].name == "Independiente del Valle"

    def test_alias_bsc(self, session):
        _seed_teams(session)
        result = find_teams_by_name(session, "BSC")
        assert "Barcelona SC" in result[0].name

    def test_alias_case_insensitive(self, session):
        _seed_teams(session)
        result = find_teams_by_name(session, "idv")
        assert result[0].name == "Independiente del Valle"
        result = find_teams_by_name(session, "Idv")
        assert result[0].name == "Independiente del Valle"

    def test_alias_manu(self, session):
        _seed_teams(session)
        result = find_teams_by_name(session, "ManU")
        assert "Manchester United" in result[0].name

    def test_returns_multiple_rows_for_multi_league_team(self, session):
        """Real Madrid exists in PD + CL → both rows returned."""
        _seed_teams(session)
        result = find_teams_by_name(session, "Real Madrid")
        assert len(result) == 2
        assert {t.league for t in result} == {"PD", "CL"}

    def test_not_found_raises_with_aliases_listed(self, session):
        _seed_teams(session)
        with pytest.raises(TeamSearchError, match="Aliases conocidos"):
            find_teams_by_name(session, "Tigres del Norte")

    def test_not_found_suggests_similar_teams(self, session):
        _seed_teams(session)
        # "Liverpoo" should suggest "Liverpool FC"
        with pytest.raises(TeamSearchError, match="Liverpool"):
            find_teams_by_name(session, "Liverpoo Reds")


# --- resolve_matchup ---

class TestResolveMatchup:

    def test_same_domestic_league(self, session):
        teams = _seed_teams(session)
        idv = find_teams_by_name(session, "IDV")
        ldu = find_teams_by_name(session, "LDU")
        home, away, league = resolve_matchup(idv, ldu)
        assert league == "EC1"
        assert home.name == "Independiente del Valle"
        assert away.name == "LDU"

    def test_prefers_domestic_over_international(self, session):
        """Real Madrid (PD+CL) vs another PD team → use PD, not CL."""
        _seed_teams(session)
        # Add a Spanish team only in PD
        atletico = Team(name="Atlético de Madrid", slug="atletico", league="PD", country="Spain")
        session.add(atletico)
        session.commit()

        rm = find_teams_by_name(session, "Real Madrid")
        atm = find_teams_by_name(session, "Atlético")
        home, away, league = resolve_matchup(rm, atm)
        assert league == "PD"  # not CL

    def test_uses_international_when_no_domestic_share(self, session):
        """Real Madrid (PD+CL) vs Liverpool (PL+CL) → CL is only shared."""
        _seed_teams(session)
        rm = find_teams_by_name(session, "Real Madrid")
        liverpool = find_teams_by_name(session, "Liverpool")
        home, away, league = resolve_matchup(rm, liverpool)
        assert league == "CL"

    def test_refuses_when_no_shared_league(self, session):
        _seed_teams(session)
        bsc = find_teams_by_name(session, "BSC")
        bayern = find_teams_by_name(session, "Bayern")
        with pytest.raises(TeamSearchError, match="no comparten liga"):
            resolve_matchup(bsc, bayern)

    def test_force_overrides_no_shared_league(self, session):
        _seed_teams(session)
        bsc = find_teams_by_name(session, "BSC")
        bayern = find_teams_by_name(session, "Bayern")
        # Should not raise with force=True
        home, away, league = resolve_matchup(bsc, bayern, force=True)
        assert home.name == "Barcelona SC Guayaquil"
        # Bayern row is from BL1 league
        assert league == "EC1"  # home's league


# --- Sanity ---

class TestAliasesIntegrity:

    def test_all_aliases_lowercase_keys(self):
        """Aliases must have lowercase keys for case-insensitive lookup."""
        for key in TEAM_ALIASES:
            assert key == key.lower(), f"Alias '{key}' should be lowercase"

    def test_alias_values_are_strings(self):
        for value in TEAM_ALIASES.values():
            assert isinstance(value, str)
            assert len(value) > 0
