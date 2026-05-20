"""Integration tests for BankrollTracker.

Uses real SQLite (in-memory) — tests the actual SQL queries + ORM behavior.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from core.bankroll.tracker import BankrollError, BankrollTracker, RoiReport
from db.base import Base
from db.enums import BetOutcome, League, PredictionVerdict
from db.models import BankrollSnapshot, Bet, Prediction, Team


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

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


@pytest.fixture
def tracker(session):
    return BankrollTracker(session)


_prediction_counter = {"n": 0}


def _create_prediction(session, *, league=League.PREMIER_LEAGUE.value) -> Prediction:
    """Helper: create a Prediction with valid teams + numbers.

    Each call generates unique team slugs to avoid (slug, league) UNIQUE violation
    when a test creates multiple predictions.
    """
    _prediction_counter["n"] += 1
    n = _prediction_counter["n"]
    home = Team(name=f"Home {n}", slug=f"home-{n}", league=league)
    away = Team(name=f"Away {n}", slug=f"away-{n}", league=league)
    session.add_all([home, away])
    session.commit()

    pred = Prediction(
        home_team_id=home.id,
        away_team_id=away.id,
        match_date=datetime.now(timezone.utc) + timedelta(days=1),
        league=league,
        model_version="test_v1",
        pre_score=65.0, implied_prob=50.0, my_prob=60.0,
        ev=2.0, kelly_fraction=0.05,
        quota=2.0, stake=10.0,
        verdict=PredictionVerdict.APOSTAR.value,
    )
    session.add(pred)
    session.commit()
    return pred


# --- Balance reads ---

class TestBalanceReads:

    def test_empty_bankroll_returns_zero(self, tracker):
        assert tracker.get_current_balance() == 0.0

    def test_balance_after_deposit(self, tracker):
        tracker.deposit(150.0)
        assert tracker.get_current_balance() == 150.0

    def test_pending_commitment_zero_when_no_bets(self, tracker):
        assert tracker.get_pending_commitment() == 0.0

    def test_available_balance_subtracts_pending(self, tracker, session):
        pred = _create_prediction(session)
        tracker.deposit(150.0)
        tracker.place_bet(pred.id, quota=2.0, stake=20.0)

        assert tracker.get_current_balance() == 150.0  # balance unchanged
        assert tracker.get_pending_commitment() == 20.0  # 20 committed
        assert tracker.get_available_balance() == 130.0  # 150 - 20


# --- Deposit ---

class TestDeposit:

    def test_deposit_increases_balance(self, tracker):
        tracker.deposit(100.0)
        tracker.deposit(50.0)
        assert tracker.get_current_balance() == 150.0

    def test_deposit_negative_raises(self, tracker):
        with pytest.raises(BankrollError, match="must be > 0"):
            tracker.deposit(-10.0)

    def test_deposit_zero_raises(self, tracker):
        with pytest.raises(BankrollError, match="must be > 0"):
            tracker.deposit(0.0)


# --- Withdrawal ---

class TestWithdraw:

    def test_withdraw_decreases_balance(self, tracker):
        tracker.deposit(150.0)
        tracker.withdraw(40.0)
        assert tracker.get_current_balance() == 110.0

    def test_withdraw_more_than_available_raises(self, tracker):
        tracker.deposit(100.0)
        with pytest.raises(BankrollError, match="Insufficient available"):
            tracker.withdraw(200.0)

    def test_cannot_withdraw_committed_capital(self, tracker, session):
        """Pending bets lock capital — can't withdraw what's committed."""
        pred = _create_prediction(session)
        tracker.deposit(100.0)
        tracker.place_bet(pred.id, quota=2.0, stake=80.0)  # locks 80

        # Available is 20, can't withdraw 50
        with pytest.raises(BankrollError, match="Insufficient available"):
            tracker.withdraw(50.0)
        # But can withdraw 20
        tracker.withdraw(20.0)
        assert tracker.get_available_balance() == 0.0


# --- Place bet ---

class TestPlaceBet:

    def test_place_bet_creates_pending_bet(self, tracker, session):
        pred = _create_prediction(session)
        tracker.deposit(100.0)
        bet = tracker.place_bet(pred.id, quota=2.5, stake=15.0)

        assert bet.outcome == BetOutcome.PENDING.value
        assert bet.stake_amount == 15.0
        assert bet.quota_used == 2.5
        assert bet.prediction_id == pred.id

    def test_place_bet_does_not_change_balance(self, tracker, session):
        """Place commits stake but balance only changes on settle."""
        pred = _create_prediction(session)
        tracker.deposit(100.0)
        balance_before = tracker.get_current_balance()
        tracker.place_bet(pred.id, quota=2.0, stake=10.0)
        assert tracker.get_current_balance() == balance_before

    def test_place_bet_insufficient_available_raises(self, tracker, session):
        pred = _create_prediction(session)
        tracker.deposit(50.0)
        with pytest.raises(BankrollError, match="Insufficient available"):
            tracker.place_bet(pred.id, quota=2.0, stake=100.0)

    def test_place_bet_invalid_quota_raises(self, tracker, session):
        pred = _create_prediction(session)
        tracker.deposit(100.0)
        with pytest.raises(BankrollError, match="Quota must be > 1.0"):
            tracker.place_bet(pred.id, quota=0.9, stake=10.0)

    def test_place_bet_nonexistent_prediction_raises(self, tracker):
        tracker.deposit(100.0)
        with pytest.raises(BankrollError, match="not found"):
            tracker.place_bet(99999, quota=2.0, stake=10.0)


# --- Settle bet ---

class TestSettleBet:

    def test_settle_won_adds_profit_to_balance(self, tracker, session):
        pred = _create_prediction(session)
        tracker.deposit(150.0)
        bet = tracker.place_bet(pred.id, quota=2.0, stake=10.0)
        settled, snapshot = tracker.settle_bet(bet.id, BetOutcome.WON)

        # Profit = (2.0 - 1.0) * 10 = 10
        assert settled.outcome == BetOutcome.WON.value
        assert settled.payout_amount == 20.0  # stake + profit
        assert snapshot.change_amount == 10.0
        assert tracker.get_current_balance() == 160.0  # 150 + 10 profit

    def test_settle_lost_subtracts_stake(self, tracker, session):
        pred = _create_prediction(session)
        tracker.deposit(150.0)
        bet = tracker.place_bet(pred.id, quota=2.0, stake=10.0)
        settled, snapshot = tracker.settle_bet(bet.id, BetOutcome.LOST)

        assert settled.outcome == BetOutcome.LOST.value
        assert settled.payout_amount == 0.0
        assert snapshot.change_amount == -10.0
        assert tracker.get_current_balance() == 140.0

    def test_settle_void_returns_no_snapshot(self, tracker, session):
        pred = _create_prediction(session)
        tracker.deposit(150.0)
        bet = tracker.place_bet(pred.id, quota=2.0, stake=10.0)
        settled, snapshot = tracker.settle_bet(bet.id, BetOutcome.VOID)

        assert settled.outcome == BetOutcome.VOID.value
        assert settled.payout_amount == 10.0  # full refund
        assert snapshot is None
        assert tracker.get_current_balance() == 150.0  # unchanged

    def test_cannot_settle_twice(self, tracker, session):
        pred = _create_prediction(session)
        tracker.deposit(150.0)
        bet = tracker.place_bet(pred.id, quota=2.0, stake=10.0)
        tracker.settle_bet(bet.id, BetOutcome.WON)

        with pytest.raises(BankrollError, match="already settled"):
            tracker.settle_bet(bet.id, BetOutcome.LOST)

    def test_settle_nonexistent_bet_raises(self, tracker):
        with pytest.raises(BankrollError, match="not found"):
            tracker.settle_bet(99999, BetOutcome.WON)

    def test_settling_releases_pending_commitment(self, tracker, session):
        pred = _create_prediction(session)
        tracker.deposit(100.0)
        bet = tracker.place_bet(pred.id, quota=2.0, stake=30.0)
        assert tracker.get_pending_commitment() == 30.0

        tracker.settle_bet(bet.id, BetOutcome.WON)
        assert tracker.get_pending_commitment() == 0.0


# --- ROI reporting ---

class TestRoi:

    def test_empty_history_returns_zero_roi(self, tracker):
        report = tracker.compute_roi()
        assert isinstance(report, RoiReport)
        assert report.bets_settled == 0
        assert report.roi_pct == 0.0

    def test_pending_bets_excluded(self, tracker, session):
        pred = _create_prediction(session)
        tracker.deposit(100.0)
        tracker.place_bet(pred.id, quota=2.0, stake=10.0)
        report = tracker.compute_roi()
        assert report.bets_settled == 0

    def test_winning_bets_increase_roi(self, tracker, session):
        tracker.deposit(150.0)
        for _ in range(3):
            pred = _create_prediction(session)
            bet = tracker.place_bet(pred.id, quota=2.0, stake=10.0)
            tracker.settle_bet(bet.id, BetOutcome.WON)

        report = tracker.compute_roi()
        assert report.bets_settled == 3
        assert report.bets_won == 3
        assert report.total_staked == 30.0
        assert report.total_returned == 60.0
        assert report.net_profit == 30.0
        assert report.roi_pct == 100.0  # doubled the staked amount

    def test_losing_bets_decrease_roi(self, tracker, session):
        tracker.deposit(150.0)
        for _ in range(2):
            pred = _create_prediction(session)
            bet = tracker.place_bet(pred.id, quota=2.0, stake=10.0)
            tracker.settle_bet(bet.id, BetOutcome.LOST)

        report = tracker.compute_roi()
        assert report.bets_lost == 2
        assert report.net_profit == -20.0
        assert report.roi_pct == -100.0

    def test_mixed_outcomes_realistic_roi(self, tracker, session):
        """3 wins, 2 losses at quota 2.0 = +1 net unit = +20% ROI."""
        tracker.deposit(200.0)
        outcomes = [BetOutcome.WON] * 3 + [BetOutcome.LOST] * 2
        for outcome in outcomes:
            pred = _create_prediction(session)
            bet = tracker.place_bet(pred.id, quota=2.0, stake=10.0)
            tracker.settle_bet(bet.id, outcome)

        report = tracker.compute_roi()
        # 3 won × 10 profit = +30
        # 2 lost × 10 stake = -20
        # net +10 on 50 staked = +20%
        assert report.bets_won == 3
        assert report.bets_lost == 2
        assert report.total_staked == 50.0
        assert report.net_profit == pytest.approx(10.0)
        assert report.roi_pct == pytest.approx(20.0)

    def test_void_bets_excluded_from_roi_calculation(self, tracker, session):
        """Void = full refund, shouldn't affect ROI numerator or denominator."""
        tracker.deposit(150.0)

        pred1 = _create_prediction(session)
        bet1 = tracker.place_bet(pred1.id, quota=2.0, stake=10.0)
        tracker.settle_bet(bet1.id, BetOutcome.WON)

        pred2 = _create_prediction(session)
        bet2 = tracker.place_bet(pred2.id, quota=2.0, stake=20.0)
        tracker.settle_bet(bet2.id, BetOutcome.VOID)

        report = tracker.compute_roi()
        assert report.bets_void == 1
        assert report.total_staked == 10.0  # void excluded
        assert report.net_profit == 10.0
        assert report.roi_pct == 100.0


# --- Realistic workflow ---

class TestRealisticWorkflow:

    def test_full_lifecycle_150_bankroll(self, tracker, session):
        """Tu hermano: starts with $150, makes 3 bets, ends with new balance."""
        tracker.deposit(150.0)
        assert tracker.get_current_balance() == 150.0

        # Bet 1: Win at quota 2.0 with $10 stake → +$10
        pred1 = _create_prediction(session)
        bet1 = tracker.place_bet(pred1.id, quota=2.0, stake=10.0)
        tracker.settle_bet(bet1.id, BetOutcome.WON)
        assert tracker.get_current_balance() == 160.0

        # Bet 2: Lose at quota 1.8 with $15 stake → -$15
        pred2 = _create_prediction(session)
        bet2 = tracker.place_bet(pred2.id, quota=1.8, stake=15.0)
        tracker.settle_bet(bet2.id, BetOutcome.LOST)
        assert tracker.get_current_balance() == 145.0

        # Bet 3: Win at quota 3.0 with $5 stake → +$10
        pred3 = _create_prediction(session)
        bet3 = tracker.place_bet(pred3.id, quota=3.0, stake=5.0)
        tracker.settle_bet(bet3.id, BetOutcome.WON)
        assert tracker.get_current_balance() == 155.0

        # ROI check: staked $30, won $25, lost $15 = net +$5 / $30 = 16.67%
        report = tracker.compute_roi()
        assert report.bets_settled == 3
        assert report.bets_won == 2
        assert report.bets_lost == 1
        assert report.total_staked == 30.0
        assert report.net_profit == pytest.approx(5.0)
        assert report.roi_pct == pytest.approx(16.67, abs=0.1)
