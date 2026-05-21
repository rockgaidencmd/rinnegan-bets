"""Tests for /api/fixtures — upcoming matches endpoint."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.app import create_app
from db.base import Base
from db.database import get_db
from db.enums import League
from db.models import Team


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


def _mock_sofascore_payload(home_sofa_id=5255, away_sofa_id=5257):
    """Fake SofaScore upcoming-events payload."""
    future = int((datetime.now(timezone.utc) + timedelta(days=2)).timestamp())
    return {
        "events": [{
            "id": 9001,
            "status": {"type": "notstarted"},
            "tournament": {"uniqueTournament": {"id": 240}},  # EC1
            "homeTeam": {"id": home_sofa_id, "name": "Emelec"},
            "awayTeam": {"id": away_sofa_id, "name": "LDU"},
            "startTimestamp": future,
        }],
        "hasNextPage": False,
    }


def _mock_seasons_payload():
    return {"seasons": [{"id": 89674, "name": "LigaPro 2026"}]}


class TestFixturesEndpoint:

    def test_unknown_league_returns_404(self, client):
        resp = client.get("/api/fixtures?league=XYZ")
        assert resp.status_code == 404

    def test_missing_league_returns_422(self, client):
        resp = client.get("/api/fixtures")
        assert resp.status_code == 422

    @patch("api.routes.fixtures.SofaScoreFetcher")
    def test_returns_upcoming_fixture_with_team_ids(self, MockFetcher, client, db):
        # Seed teams with sofascore_ids that match the mock payload
        emelec = Team(
            name="Emelec", slug="emelec",
            league=League.LIGA_PRO_ECUADOR.value, country="Ecuador",
            sofascore_id=5255,
        )
        ldu = Team(
            name="LDU", slug="ldu",
            league=League.LIGA_PRO_ECUADOR.value, country="Ecuador",
            sofascore_id=5257,
        )
        db.add_all([emelec, ldu])
        db.commit()

        instance = MockFetcher.return_value
        instance.get_tournament_seasons.return_value = _mock_seasons_payload()
        instance.get_tournament_upcoming.return_value = _mock_sofascore_payload()

        resp = client.get("/api/fixtures?league=EC1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["league"] == "EC1"
        assert data["total"] == 1
        f = data["fixtures"][0]
        assert f["home_team_name"] == "Emelec"
        assert f["away_team_name"] == "LDU"
        assert f["home_team_id"] == emelec.id
        assert f["away_team_id"] == ldu.id

    @patch("api.routes.fixtures.SofaScoreFetcher")
    def test_teams_not_in_db_return_null_ids(self, MockFetcher, client):
        instance = MockFetcher.return_value
        instance.get_tournament_seasons.return_value = _mock_seasons_payload()
        instance.get_tournament_upcoming.return_value = _mock_sofascore_payload(
            home_sofa_id=99999, away_sofa_id=88888,
        )

        resp = client.get("/api/fixtures?league=EC1")
        assert resp.status_code == 200
        f = resp.json()["fixtures"][0]
        assert f["home_team_id"] is None
        assert f["away_team_id"] is None

    @patch("api.routes.fixtures.SofaScoreFetcher")
    def test_days_filter_excludes_far_future(self, MockFetcher, client):
        far_future = int((datetime.now(timezone.utc) + timedelta(days=20)).timestamp())
        payload = {"events": [{
            "id": 1, "status": {"type": "notstarted"},
            "tournament": {"uniqueTournament": {"id": 240}},
            "homeTeam": {"id": 1, "name": "A"}, "awayTeam": {"id": 2, "name": "B"},
            "startTimestamp": far_future,
        }]}
        instance = MockFetcher.return_value
        instance.get_tournament_seasons.return_value = _mock_seasons_payload()
        instance.get_tournament_upcoming.return_value = payload

        # days=7 should exclude this
        resp = client.get("/api/fixtures?league=EC1&days=7")
        assert resp.json()["total"] == 0
        # days=30 should include it
        resp = client.get("/api/fixtures?league=EC1&days=30")
        assert resp.json()["total"] == 1
