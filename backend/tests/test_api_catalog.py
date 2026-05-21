"""Tests for catalog endpoints: leagues, teams listing, matches."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.app import create_app
from db.base import Base
from db.database import get_db
from db.enums import League
from db.models import Match, Team


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def _fk_on(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def TestSession(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def client(engine, TestSession):
    app = create_app()

    def _override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db(TestSession):
    s = TestSession()
    try:
        yield s
    finally:
        s.close()


def _seed_catalog(db):
    """Seed 2 leagues with 2 teams + 2 matches each."""
    teams = [
        Team(name="Arsenal", slug="arsenal", league=League.PREMIER_LEAGUE.value, country="England"),
        Team(name="Liverpool", slug="liverpool", league=League.PREMIER_LEAGUE.value, country="England"),
        Team(name="Barca", slug="barca", league=League.LA_LIGA.value, country="Spain"),
        Team(name="Real", slug="real", league=League.LA_LIGA.value, country="Spain"),
    ]
    db.add_all(teams)
    db.commit()

    now = datetime.now(timezone.utc)
    matches = [
        Match(
            home_team_id=teams[0].id, away_team_id=teams[1].id,
            league=League.PREMIER_LEAGUE.value,
            match_date=now - timedelta(days=2),
            home_goals=2, away_goals=1, result="H",
            home_xg=1.8, away_xg=1.2,
            source="sofascore", external_id="pl-1",
            fetched_at=now,
        ),
        Match(
            home_team_id=teams[2].id, away_team_id=teams[3].id,
            league=League.LA_LIGA.value,
            match_date=now - timedelta(days=1),
            home_goals=3, away_goals=2, result="H",
            home_xg=2.4, away_xg=1.9,
            source="sofascore", external_id="la-1",
            fetched_at=now,
        ),
    ]
    db.add_all(matches)
    db.commit()
    return teams, matches


# --- /api/leagues ---

class TestLeagueList:

    def test_lists_all_leagues_with_counts(self, client, db):
        _seed_catalog(db)
        resp = client.get("/api/leagues")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2

        codes = {l["code"] for l in data["leagues"]}
        assert "PL" in codes
        assert "PD" in codes

        pl = next(l for l in data["leagues"] if l["code"] == "PL")
        assert pl["name"] == "Premier League"
        assert pl["team_count"] == 2
        assert pl["match_count"] == 1

    def test_empty_db_returns_all_supported_leagues_with_zero_counts(self, client):
        """Endpoint exposes the catalog from core.leagues — present even if BD is empty."""
        from core.leagues import LEAGUES
        resp = client.get("/api/leagues")
        assert resp.status_code == 200
        data = resp.json()
        # Catalog from LEAGUES is exposed regardless of DB content
        assert data["total"] == len(LEAGUES)
        # All counts are 0 since DB is empty
        for league in data["leagues"]:
            assert league["team_count"] == 0
            assert league["match_count"] == 0


# --- /api/leagues/{code}/teams ---

class TestTeamsByLeague:

    def test_returns_teams_alphabetically(self, client, db):
        _seed_catalog(db)
        resp = client.get("/api/leagues/PL/teams")
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()]
        assert names == ["Arsenal", "Liverpool"]

    def test_unknown_league_returns_404(self, client):
        resp = client.get("/api/leagues/XYZ/teams")
        assert resp.status_code == 404


# --- /api/matches ---

class TestMatchList:

    def test_lists_recent_matches(self, client, db):
        _seed_catalog(db)
        resp = client.get("/api/matches")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        # Most recent first
        assert data["matches"][0]["league"] == "PD"  # La Liga (1 day ago)
        assert data["matches"][1]["league"] == "PL"  # Premier (2 days ago)

    def test_filter_by_league(self, client, db):
        _seed_catalog(db)
        resp = client.get("/api/matches?league=PL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["matches"][0]["league"] == "PL"

    def test_filter_by_team(self, client, db):
        teams, _ = _seed_catalog(db)
        resp = client.get(f"/api/matches?team_id={teams[0].id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["matches"][0]["home_team_id"] == teams[0].id

    def test_includes_team_names_and_xg(self, client, db):
        _seed_catalog(db)
        resp = client.get("/api/matches?limit=1")
        match = resp.json()["matches"][0]
        assert match["home_team_name"]
        assert match["away_team_name"]
        assert match["home_xg"] is not None
        assert match["home_goals"] is not None

    def test_limit_param_respected(self, client, db):
        _seed_catalog(db)
        resp = client.get("/api/matches?limit=1")
        assert resp.json()["total"] == 1

    def test_pagination_offset_returns_next_page(self, client, db):
        """offset=N skips first N rows; total_available stays constant."""
        _seed_catalog(db)  # 2 matches
        page1 = client.get("/api/matches?limit=1&offset=0").json()
        page2 = client.get("/api/matches?limit=1&offset=1").json()
        assert page1["total"] == 1 and page2["total"] == 1
        assert page1["total_available"] == 2 and page2["total_available"] == 2
        assert page1["offset"] == 0 and page2["offset"] == 1
        assert page1["matches"][0]["id"] != page2["matches"][0]["id"]

    def test_pagination_offset_beyond_data_returns_empty_but_keeps_total(self, client, db):
        _seed_catalog(db)
        resp = client.get("/api/matches?offset=999").json()
        assert resp["total"] == 0
        assert resp["total_available"] == 2
