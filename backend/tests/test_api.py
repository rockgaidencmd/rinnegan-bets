"""Integration tests for the FastAPI HTTP layer.

Uses TestClient with an in-memory SQLite engine via dependency override.
Validates: routing, schemas, error mapping, end-to-end workflows.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.app import create_app
from db.base import Base
from db.database import get_db
from db.enums import League, PredictionVerdict
from db.models import Match, Prediction, Team


@pytest.fixture
def engine():
    # StaticPool: reuse a single connection so all sessions see the same in-memory DB.
    # Without this, each new session creates a fresh empty :memory: database.
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


def _seed_teams_with_matches(db):
    """Helper: seed two teams with finished matches that have stats."""
    barca = Team(
        name="FC Barcelona", slug="fc-barcelona",
        league=League.LA_LIGA.value, country="Spain",
    )
    rm = Team(
        name="Real Madrid CF", slug="real-madrid",
        league=League.LA_LIGA.value, country="Spain",
    )
    db.add_all([barca, rm])
    db.commit()

    now = datetime.now(timezone.utc)
    matches = []
    for i in range(5):
        matches.append(Match(
            home_team_id=barca.id, away_team_id=rm.id,
            league=League.LA_LIGA.value,
            match_date=now - timedelta(days=10 + i),
            home_goals=3, away_goals=1, result="H",
            home_xg=2.4, away_xg=0.9,
            home_possession=60.0, away_possession=40.0,
            home_shots_on_target=7, away_shots_on_target=3,
            home_corners=8, away_corners=3,
            home_yellow_cards=2, away_yellow_cards=3,
            source="sofascore", external_id=f"test-{i}",
            fetched_at=now,
        ))
    db.add_all(matches)
    db.commit()
    return barca, rm


# --- Health ---

class TestHealth:

    def test_healthcheck_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# --- Teams ---

class TestTeams:

    def test_search_returns_results(self, client, db):
        _seed_teams_with_matches(db)
        resp = client.get("/api/teams/search?q=Barcelona")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        assert any("Barcelona" in t["name"] for t in data["results"])

    def test_search_resolves_alias(self, client, db):
        _seed_teams_with_matches(db)
        # Add IDV-aliased team
        idv = Team(name="Independiente del Valle", slug="idv",
                   league=League.LIGA_PRO_ECUADOR.value, country="Ecuador")
        db.add(idv)
        db.commit()

        resp = client.get("/api/teams/search?q=IDV")
        assert resp.status_code == 200
        assert any("Independiente" in t["name"] for t in resp.json()["results"])

    def test_search_not_found_returns_404(self, client):
        resp = client.get("/api/teams/search?q=NoExisteEsteEquipo")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_search_requires_q_param(self, client):
        resp = client.get("/api/teams/search")
        assert resp.status_code == 422  # missing required param

    def test_get_team_by_id(self, client, db):
        barca, _ = _seed_teams_with_matches(db)
        resp = client.get(f"/api/teams/{barca.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "FC Barcelona"

    def test_get_team_unknown_id_returns_404(self, client):
        resp = client.get("/api/teams/99999")
        assert resp.status_code == 404

    def test_team_stats_returns_aggregates(self, client, db):
        barca, _ = _seed_teams_with_matches(db)
        resp = client.get(f"/api/teams/{barca.id}/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["matches_analyzed"] == 5
        assert data["wins"] == 5
        assert data["avg_xg_for"] == pytest.approx(2.4)
        assert data["form_score"] == pytest.approx(100.0)


# --- Predictions ---

class TestPredictions:

    def test_predict_returns_full_response(self, client, db):
        _seed_teams_with_matches(db)
        resp = client.post("/api/predictions", json={
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
            "quota": 2.0,
            "stake": 10.0,
            "importance": "clasif",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["home_team"] == "FC Barcelona"
        assert data["away_team"] == "Real Madrid CF"
        assert data["league"] == "PD"
        assert data["verdict"] in {"apostar", "esperar", "no_apostar"}
        assert 0 <= data["my_prob"] <= 1
        assert 0 <= data["pre_score"] <= 100
        assert data["model_version"] == "europe_v1"

    def test_predict_invalid_quota_returns_422(self, client, db):
        _seed_teams_with_matches(db)
        resp = client.post("/api/predictions", json={
            "home_team": "Barcelona", "away_team": "Real Madrid",
            "quota": 0.9, "stake": 10.0,  # quota must be > 1
        })
        assert resp.status_code == 422

    def test_predict_unknown_team_returns_404(self, client):
        resp = client.post("/api/predictions", json={
            "home_team": "NoExistente FC", "away_team": "Real Madrid",
            "quota": 2.0, "stake": 10.0,
        })
        assert resp.status_code == 404


# --- Bankroll ---

class TestBankroll:

    def test_balance_empty_returns_zero(self, client):
        resp = client.get("/api/bankroll")
        assert resp.status_code == 200
        assert resp.json() == {"current": 0.0, "available": 0.0, "pending_commitment": 0.0}

    def test_deposit_then_balance(self, client):
        resp = client.post("/api/bankroll/deposit", json={"amount": 150.0})
        assert resp.status_code == 201
        snap = resp.json()
        assert snap["balance"] == 150.0
        assert snap["reason"] == "deposit"

        resp = client.get("/api/bankroll")
        assert resp.json()["current"] == 150.0

    def test_deposit_negative_returns_422_from_pydantic(self, client):
        resp = client.post("/api/bankroll/deposit", json={"amount": -5})
        assert resp.status_code == 422

    def test_withdraw_insufficient_returns_422(self, client):
        resp = client.post("/api/bankroll/withdraw", json={"amount": 999})
        assert resp.status_code == 422
        assert "Insufficient" in resp.json()["detail"]

    def test_settle_unknown_bet_returns_404(self, client):
        resp = client.post(
            "/api/bankroll/bets/9999/settle",
            json={"outcome": "won"},
        )
        assert resp.status_code == 404


# --- Full workflow ---

class TestFullWorkflow:

    def test_predict_then_place_bet_then_settle_won(self, client, db):
        """End-to-end: deposit $150, predict, place bet, settle, ROI updates."""
        _seed_teams_with_matches(db)

        # 1. Deposit
        client.post("/api/bankroll/deposit", json={"amount": 150.0})

        # 2. Predict (also creates Prediction row via direct DB for now)
        prediction = Prediction(
            home_team_id=1, away_team_id=2,
            match_date=datetime.now(timezone.utc) + timedelta(days=1),
            league=League.LA_LIGA.value, model_version="europe_v1",
            pre_score=70.0, implied_prob=50.0, my_prob=65.0,
            ev=3.0, kelly_fraction=0.1,
            quota=2.0, stake=10.0,
            verdict=PredictionVerdict.APOSTAR.value,
        )
        db.add(prediction)
        db.commit()

        # 3. Place bet
        resp = client.post("/api/bankroll/bets", json={
            "prediction_id": prediction.id, "quota": 2.0, "stake": 10.0,
        })
        assert resp.status_code == 201
        bet_id = resp.json()["id"]

        # 4. Verify committed capital
        resp = client.get("/api/bankroll")
        assert resp.json()["available"] == 140.0
        assert resp.json()["pending_commitment"] == 10.0

        # 5. Settle as won
        resp = client.post(
            f"/api/bankroll/bets/{bet_id}/settle",
            json={"outcome": "won"},
        )
        assert resp.status_code == 200
        assert resp.json()["bet"]["outcome"] == "won"

        # 6. Balance should now be 160 (150 - 10 + 20)
        resp = client.get("/api/bankroll")
        assert resp.json()["current"] == 160.0

        # 7. ROI shows 1 settled, +$10 net
        resp = client.get("/api/bankroll/roi")
        roi = resp.json()
        assert roi["bets_settled"] == 1
        assert roi["bets_won"] == 1
        assert roi["net_profit"] == 10.0
