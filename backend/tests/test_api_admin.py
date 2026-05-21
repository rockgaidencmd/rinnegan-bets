"""Tests for admin endpoints (stats + manual refresh trigger)."""

from datetime import datetime, timezone
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


def _seed(db):
    home = Team(name="A", slug="a", league=League.PREMIER_LEAGUE.value)
    away = Team(name="B", slug="b", league=League.PREMIER_LEAGUE.value)
    db.add_all([home, away])
    db.commit()
    db.add(Match(
        home_team_id=home.id, away_team_id=away.id,
        league=League.PREMIER_LEAGUE.value,
        match_date=datetime.now(timezone.utc),
        home_goals=2, away_goals=1, result="H",
        home_xg=1.5, away_xg=1.0,
        source="sofascore", external_id="t-1",
        fetched_at=datetime.now(timezone.utc),
    ))
    db.commit()


class TestAdminStats:

    def test_empty_db_returns_zeros(self, client):
        resp = client.get("/api/admin/stats")
        assert resp.status_code == 200
        assert resp.json() == {
            "teams": 0, "matches": 0,
            "matches_with_xg": 0, "leagues_with_data": 0,
        }

    def test_stats_reflect_seeded_data(self, client, db):
        _seed(db)
        resp = client.get("/api/admin/stats")
        assert resp.json() == {
            "teams": 2, "matches": 1,
            "matches_with_xg": 1, "leagues_with_data": 1,
        }


class TestAdminRefresh:

    @patch("api.routes.admin._run_seed_matches")
    def test_refresh_returns_202_and_schedules_task(self, mock_run, client, db):
        _seed(db)
        resp = client.post("/api/admin/refresh", json={})
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "started"
        assert body["teams_before"] == 2
        assert body["matches_before"] == 1
        # The TestClient runs background tasks synchronously when the request returns
        mock_run.assert_called_once()
