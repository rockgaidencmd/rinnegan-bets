"""Integration tests for DB models.

Uses SQLite in-memory DB — fast, isolated, no leftover state.
Tests verify real ORM behavior: FKs, CHECK constraints, JSON columns,
timestamps, cascade rules.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from db.enums import (
    BankrollReason,
    BetOutcome,
    DataSource,
    League,
    MatchResult,
    PredictionVerdict,
)
from db.models import (
    BankrollSnapshot,
    Bet,
    DataCache,
    Match,
    ModelPerformance,
    Prediction,
    Team,
)


# --- Fixtures ---

@pytest.fixture
def session() -> Session:
    """Fresh in-memory SQLite DB per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Enable FK enforcement (same as production database.py)
    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _utc(year, month, day, hour=0, minute=0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def _make_team(session, name="Barcelona", league=League.LA_LIGA) -> Team:
    team = Team(
        name=name,
        slug=name.lower().replace(" ", "-"),
        league=league.value,
        country="Spain",
    )
    session.add(team)
    session.commit()
    return team


# --- Team tests ---

class TestTeam:

    def test_create_and_retrieve(self, session):
        team = _make_team(session, "Barcelona")
        assert team.id is not None
        assert team.created_at is not None
        assert team.updated_at is not None

        retrieved = session.get(Team, team.id)
        assert retrieved.name == "Barcelona"

    def test_invalid_league_rejected_by_check_constraint(self, session):
        team = Team(name="Fake", slug="fake", league="INVALID_LEAGUE")
        session.add(team)
        with pytest.raises(IntegrityError, match="ck_teams_league"):
            session.commit()

    def test_unique_slug_per_league_enforced(self, session):
        _make_team(session, "Barcelona", League.LA_LIGA)
        dup = Team(
            name="Barcelona Different", slug="barcelona", league=League.LA_LIGA.value
        )
        session.add(dup)
        # SQLite's error message doesn't include constraint name, just "UNIQUE constraint failed"
        with pytest.raises(IntegrityError, match="UNIQUE constraint failed: teams.slug"):
            session.commit()

    def test_same_slug_different_league_allowed(self, session):
        _make_team(session, "Barcelona", League.LA_LIGA)
        # Could exist a "Barcelona" team in Ecuador (theoretical)
        same_slug_other_league = Team(
            name="Barcelona EC",
            slug="barcelona",
            league=League.LIGA_PRO_ECUADOR.value,
        )
        session.add(same_slug_other_league)
        session.commit()  # Should not raise
        assert same_slug_other_league.id is not None


# --- Match tests ---

class TestMatch:

    def test_create_match_with_relationships(self, session):
        home = _make_team(session, "Barcelona")
        away = _make_team(session, "Real Madrid")

        match = Match(
            home_team_id=home.id,
            away_team_id=away.id,
            league=League.LA_LIGA.value,
            match_date=_utc(2025, 5, 1, 20),
            home_goals=3,
            away_goals=1,
            result=MatchResult.HOME_WIN.value,
            home_xg=2.4,
            away_xg=0.9,
            source=DataSource.SOFASCORE.value,
            external_id="sofa-12345",
            fetched_at=_utc(2025, 5, 2),
        )
        session.add(match)
        session.commit()

        retrieved = session.get(Match, match.id)
        assert retrieved.home_team.name == "Barcelona"
        assert retrieved.away_team.name == "Real Madrid"
        assert retrieved.home_xg == 2.4

    def test_invalid_result_rejected(self, session):
        home = _make_team(session, "Barcelona")
        away = _make_team(session, "Real Madrid")

        match = Match(
            home_team_id=home.id,
            away_team_id=away.id,
            league=League.LA_LIGA.value,
            match_date=_utc(2025, 5, 1),
            result="X",  # Invalid: only H/D/A
            source=DataSource.SOFASCORE.value,
            fetched_at=_utc(2025, 5, 2),
        )
        session.add(match)
        with pytest.raises(IntegrityError, match="ck_matches_result"):
            session.commit()

    def test_unique_source_external_id_prevents_duplicates(self, session):
        home = _make_team(session, "Barcelona")
        away = _make_team(session, "Real Madrid")

        m1 = Match(
            home_team_id=home.id, away_team_id=away.id,
            league=League.LA_LIGA.value, match_date=_utc(2025, 5, 1),
            source=DataSource.SOFASCORE.value, external_id="sofa-99",
            fetched_at=_utc(2025, 5, 2),
        )
        session.add(m1)
        session.commit()

        m2 = Match(
            home_team_id=home.id, away_team_id=away.id,
            league=League.LA_LIGA.value, match_date=_utc(2025, 5, 1),
            source=DataSource.SOFASCORE.value, external_id="sofa-99",  # duplicate
            fetched_at=_utc(2025, 5, 2),
        )
        session.add(m2)
        with pytest.raises(IntegrityError, match="UNIQUE constraint failed: matches.source"):
            session.commit()

    def test_cannot_delete_team_with_matches(self, session):
        """ondelete=RESTRICT should prevent dangling FKs."""
        home = _make_team(session, "Barcelona")
        away = _make_team(session, "Real Madrid")

        match = Match(
            home_team_id=home.id, away_team_id=away.id,
            league=League.LA_LIGA.value, match_date=_utc(2025, 5, 1),
            source=DataSource.SOFASCORE.value, external_id="sofa-1",
            fetched_at=_utc(2025, 5, 2),
        )
        session.add(match)
        session.commit()

        session.delete(home)
        with pytest.raises(IntegrityError):
            session.commit()


# --- DataCache tests ---

class TestDataCache:

    def test_set_and_retrieve(self, session):
        now = datetime.now(timezone.utc)
        cache = DataCache(
            key="fd:matches:PL:2025-05-19",
            payload={"matches": [{"id": 1}]},
            fetched_at=now,
            expires_at=now + timedelta(hours=24),
        )
        session.add(cache)
        session.commit()

        retrieved = session.get(DataCache, "fd:matches:PL:2025-05-19")
        assert retrieved.payload == {"matches": [{"id": 1}]}

    def test_expiration_check_via_query(self, session):
        now = datetime.now(timezone.utc)
        # Expired entry
        session.add(DataCache(
            key="old", payload={}, fetched_at=now - timedelta(days=2),
            expires_at=now - timedelta(days=1),
        ))
        # Fresh entry
        session.add(DataCache(
            key="fresh", payload={}, fetched_at=now,
            expires_at=now + timedelta(hours=12),
        ))
        session.commit()

        fresh_entries = session.execute(
            select(DataCache).where(DataCache.expires_at > now)
        ).scalars().all()
        assert len(fresh_entries) == 1
        assert fresh_entries[0].key == "fresh"

    def test_json_column_round_trip(self, session):
        """Verify nested dicts survive JSON serialization."""
        complex_payload = {
            "matches": [
                {"id": 1, "score": {"home": 2, "away": 1}},
                {"id": 2, "stats": {"xG": 1.8, "shots": [{"x": 0.5}]}},
            ],
            "count": 2,
        }
        now = datetime.now(timezone.utc)
        session.add(DataCache(
            key="complex", payload=complex_payload,
            fetched_at=now, expires_at=now + timedelta(hours=1),
        ))
        session.commit()

        retrieved = session.get(DataCache, "complex")
        assert retrieved.payload == complex_payload
        assert retrieved.payload["matches"][1]["stats"]["xG"] == 1.8


# --- Prediction + Bet + Bankroll workflow ---

class TestPredictionBetBankroll:

    def test_create_prediction_then_bet_then_bankroll_snapshot(self, session):
        """Full workflow: predict → bet → settle → bankroll updates."""
        home = _make_team(session, "Barcelona")
        away = _make_team(session, "Real Madrid")

        # 1. Create prediction
        prediction = Prediction(
            home_team_id=home.id,
            away_team_id=away.id,
            match_date=_utc(2025, 5, 20, 20),
            league=League.LA_LIGA.value,
            model_version="europe_v1",
            pre_score=72.5,
            implied_prob=50.0,
            my_prob=62.0,
            ev=2.40,
            kelly_fraction=0.08,
            quota=2.00,
            stake=10.0,
            verdict=PredictionVerdict.APOSTAR.value,
            reasoning={"top_factor": "xG_diff", "xG_diff": 1.5},
        )
        session.add(prediction)
        session.commit()

        # 2. Create bet from prediction
        bet = Bet(
            prediction_id=prediction.id,
            quota_used=2.00,
            stake_amount=10.0,
            placed_at=_utc(2025, 5, 20, 19),
            outcome=BetOutcome.PENDING.value,
        )
        session.add(bet)

        # Stake decrement from bankroll
        session.add(BankrollSnapshot(
            balance=90.0,
            change_amount=-10.0,
            reason=BankrollReason.WITHDRAWAL.value,
            created_at=_utc(2025, 5, 20, 19),
        ))
        session.commit()

        # 3. Settle bet as won
        bet.outcome = BetOutcome.WON.value
        bet.payout_amount = 20.0
        bet.settled_at = _utc(2025, 5, 20, 22)
        session.add(BankrollSnapshot(
            balance=110.0,
            change_amount=20.0,
            reason=BankrollReason.BET_WON.value,
            related_bet_id=bet.id,
            created_at=_utc(2025, 5, 20, 22),
        ))
        session.commit()

        # Verify final state
        retrieved_bet = session.get(Bet, bet.id)
        assert retrieved_bet.outcome == BetOutcome.WON.value
        assert retrieved_bet.prediction.verdict == PredictionVerdict.APOSTAR.value

        # Last snapshot = current balance
        latest = session.execute(
            select(BankrollSnapshot).order_by(BankrollSnapshot.created_at.desc())
        ).scalars().first()
        assert latest.balance == 110.0
        assert latest.related_bet_id == bet.id

    def test_prediction_rejects_quota_below_1(self, session):
        home = _make_team(session, "A")
        away = _make_team(session, "B")
        prediction = Prediction(
            home_team_id=home.id, away_team_id=away.id,
            match_date=_utc(2025, 5, 1), league=League.LA_LIGA.value,
            model_version="europe_v1",
            pre_score=50.0, implied_prob=50.0, my_prob=50.0,
            ev=0.0, kelly_fraction=0.0,
            quota=0.95,  # invalid: must be > 1
            stake=10.0, verdict=PredictionVerdict.NO_APOSTAR.value,
        )
        session.add(prediction)
        with pytest.raises(IntegrityError, match="ck_predictions_quota_positive"):
            session.commit()

    def test_prediction_rejects_score_above_100(self, session):
        home = _make_team(session, "A")
        away = _make_team(session, "B")
        prediction = Prediction(
            home_team_id=home.id, away_team_id=away.id,
            match_date=_utc(2025, 5, 1), league=League.LA_LIGA.value,
            model_version="europe_v1",
            pre_score=150.0,  # invalid
            implied_prob=50.0, my_prob=50.0, ev=0.0, kelly_fraction=0.0,
            quota=2.0, stake=10.0, verdict=PredictionVerdict.NO_APOSTAR.value,
        )
        session.add(prediction)
        with pytest.raises(IntegrityError, match="ck_predictions_pre_score_range"):
            session.commit()

    def test_bet_unique_per_prediction(self, session):
        """One bet per prediction (1:1 relationship)."""
        home = _make_team(session, "A")
        away = _make_team(session, "B")
        prediction = Prediction(
            home_team_id=home.id, away_team_id=away.id,
            match_date=_utc(2025, 5, 1), league=League.LA_LIGA.value,
            model_version="europe_v1",
            pre_score=70.0, implied_prob=50.0, my_prob=60.0,
            ev=2.0, kelly_fraction=0.05,
            quota=2.0, stake=10.0, verdict=PredictionVerdict.APOSTAR.value,
        )
        session.add(prediction)
        session.commit()

        bet1 = Bet(
            prediction_id=prediction.id, quota_used=2.0,
            stake_amount=10.0, placed_at=_utc(2025, 5, 1),
        )
        session.add(bet1)
        session.commit()

        bet2 = Bet(
            prediction_id=prediction.id, quota_used=2.0,
            stake_amount=10.0, placed_at=_utc(2025, 5, 1),
        )
        session.add(bet2)
        with pytest.raises(IntegrityError):
            session.commit()


# --- ModelPerformance tests ---

class TestModelPerformance:

    def test_create_performance_snapshot(self, session):
        perf = ModelPerformance(
            model_version="europe_v1",
            period_start=_utc(2025, 4, 1),
            period_end=_utc(2025, 4, 30),
            predictions_count=50,
            correct_count=32,
            roi_pct=8.5,
            brier_score=0.21,
        )
        session.add(perf)
        session.commit()

        retrieved = session.get(ModelPerformance, perf.id)
        assert retrieved.predictions_count == 50
        assert retrieved.correct_count == 32
        assert retrieved.roi_pct == 8.5

    def test_correct_count_cannot_exceed_predictions(self, session):
        perf = ModelPerformance(
            model_version="europe_v1",
            period_start=_utc(2025, 4, 1),
            period_end=_utc(2025, 4, 30),
            predictions_count=10,
            correct_count=15,  # invalid
        )
        session.add(perf)
        with pytest.raises(IntegrityError, match="ck_model_performance_correct_valid"):
            session.commit()


# --- Timestamp behavior ---

class TestTimestamps:

    def test_created_at_set_automatically(self, session):
        team = _make_team(session)
        assert team.created_at is not None
        # Should be very recent
        delta = datetime.now(timezone.utc) - team.created_at
        assert delta < timedelta(seconds=5)

    def test_updated_at_changes_on_update(self, session):
        team = _make_team(session)
        # SQLite strips timezone info on read — normalize both sides
        original_updated = team.updated_at.replace(tzinfo=None) if team.updated_at.tzinfo else team.updated_at

        # Wait a tiny bit and update
        import time
        time.sleep(0.05)
        team.name = "Barca"
        session.commit()
        session.refresh(team)

        new_updated = team.updated_at.replace(tzinfo=None) if team.updated_at.tzinfo else team.updated_at
        assert new_updated > original_updated
