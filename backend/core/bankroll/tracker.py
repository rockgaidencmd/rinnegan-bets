"""Bankroll tracker — persistent state for the user's betting bankroll.

Design: settle-only accounting.
  - place_bet: creates a Bet (status=PENDING), no balance snapshot
  - settle_won:  +profit (= (quota-1)*stake), snapshot reason=BET_WON
  - settle_lost: -stake, snapshot reason=BET_LOST
  - settle_void: no balance change (full refund cancels the bet)
  - deposit/withdraw: explicit user actions

Current balance = SELECT balance FROM bankroll_snapshots ORDER BY created_at DESC LIMIT 1
Available balance = current - sum(stake of pending bets)  (capital committed)
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.enums import BankrollReason, BetOutcome
from db.models import BankrollSnapshot, Bet, Prediction


class BankrollError(Exception):
    """Raised when an operation violates bankroll invariants."""


@dataclass(frozen=True)
class RoiReport:
    """Performance summary over a time window."""

    period_start: datetime | None
    period_end: datetime | None
    bets_settled: int
    bets_won: int
    bets_lost: int
    bets_void: int
    total_staked: float
    total_returned: float
    net_profit: float
    roi_pct: float            # net_profit / total_staked * 100


class BankrollTracker:
    """Manages bankroll persistence and bet lifecycle."""

    def __init__(self, session: Session):
        self._session = session

    # --- Balance reads ---

    def get_current_balance(self) -> float:
        """Latest snapshot balance, or 0.0 if no snapshots yet."""
        row = self._session.execute(
            select(BankrollSnapshot)
            .order_by(BankrollSnapshot.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        return row.balance if row else 0.0

    def get_pending_commitment(self) -> float:
        """Sum of stakes locked in pending bets (not yet settled)."""
        total = self._session.execute(
            select(func.coalesce(func.sum(Bet.stake_amount), 0.0))
            .where(Bet.outcome == BetOutcome.PENDING.value)
        ).scalar_one()
        return float(total)

    def get_available_balance(self) -> float:
        """Balance minus what's committed in pending bets."""
        return self.get_current_balance() - self.get_pending_commitment()

    # --- Deposits & withdrawals ---

    def deposit(self, amount: float) -> BankrollSnapshot:
        """Add money to the bankroll. Amount must be positive."""
        if amount <= 0:
            raise BankrollError(f"Deposit amount must be > 0, got {amount}")
        return self._record(amount, BankrollReason.DEPOSIT)

    def withdraw(self, amount: float) -> BankrollSnapshot:
        """Take money out. Cannot withdraw committed capital."""
        if amount <= 0:
            raise BankrollError(f"Withdrawal amount must be > 0, got {amount}")
        if amount > self.get_available_balance():
            raise BankrollError(
                f"Insufficient available balance: {self.get_available_balance():.2f} "
                f"(requested {amount:.2f}). Settle pending bets first."
            )
        return self._record(-amount, BankrollReason.WITHDRAWAL)

    # --- Bet lifecycle ---

    def place_bet(
        self, prediction_id: int, quota: float, stake: float,
    ) -> Bet:
        """Create a Bet record from a Prediction. Locks `stake` until settled."""
        if stake <= 0:
            raise BankrollError(f"Stake must be > 0, got {stake}")
        if quota <= 1.0:
            raise BankrollError(f"Quota must be > 1.0, got {quota}")
        if stake > self.get_available_balance():
            raise BankrollError(
                f"Insufficient available balance: {self.get_available_balance():.2f} "
                f"(stake {stake:.2f}). Deposit or settle pending bets first."
            )

        prediction = self._session.get(Prediction, prediction_id)
        if not prediction:
            raise BankrollError(f"Prediction {prediction_id} not found")

        bet = Bet(
            prediction_id=prediction_id,
            quota_used=quota,
            stake_amount=stake,
            placed_at=datetime.now(timezone.utc),
            outcome=BetOutcome.PENDING.value,
        )
        self._session.add(bet)
        self._session.commit()
        return bet

    def settle_bet(
        self, bet_id: int, outcome: BetOutcome,
    ) -> tuple[Bet, BankrollSnapshot | None]:
        """Mark bet as won/lost/void and update bankroll accordingly.

        Returns (bet, snapshot) — snapshot is None for VOID.
        """
        bet = self._session.get(Bet, bet_id)
        if not bet:
            raise BankrollError(f"Bet {bet_id} not found")
        if bet.outcome != BetOutcome.PENDING.value:
            raise BankrollError(f"Bet {bet_id} already settled as {bet.outcome}")

        bet.outcome = outcome.value
        bet.settled_at = datetime.now(timezone.utc)

        snapshot: BankrollSnapshot | None = None

        if outcome == BetOutcome.WON:
            profit = (bet.quota_used - 1.0) * bet.stake_amount
            bet.payout_amount = bet.stake_amount + profit
            snapshot = self._record(profit, BankrollReason.BET_WON, related_bet_id=bet.id)
        elif outcome == BetOutcome.LOST:
            bet.payout_amount = 0.0
            snapshot = self._record(-bet.stake_amount, BankrollReason.BET_LOST, related_bet_id=bet.id)
        elif outcome == BetOutcome.VOID:
            bet.payout_amount = bet.stake_amount  # full refund, no net change
            # No snapshot — bankroll unchanged
        else:
            raise BankrollError(f"Cannot settle as PENDING: outcome={outcome}")

        self._session.commit()
        return bet, snapshot

    # --- Reporting ---

    def compute_roi(
        self, period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> RoiReport:
        """ROI over a time window. None bounds = no limit on that side."""
        query = select(Bet).where(Bet.outcome != BetOutcome.PENDING.value)
        if period_start:
            query = query.where(Bet.settled_at >= period_start)
        if period_end:
            query = query.where(Bet.settled_at <= period_end)

        bets = self._session.execute(query).scalars().all()

        bets_won = sum(1 for b in bets if b.outcome == BetOutcome.WON.value)
        bets_lost = sum(1 for b in bets if b.outcome == BetOutcome.LOST.value)
        bets_void = sum(1 for b in bets if b.outcome == BetOutcome.VOID.value)

        # Void bets refund stake — don't count in staked/returned
        active = [b for b in bets if b.outcome != BetOutcome.VOID.value]
        total_staked = sum(b.stake_amount for b in active)
        total_returned = sum((b.payout_amount or 0.0) for b in active)
        net_profit = total_returned - total_staked
        roi_pct = (net_profit / total_staked * 100) if total_staked > 0 else 0.0

        return RoiReport(
            period_start=period_start,
            period_end=period_end,
            bets_settled=len(bets),
            bets_won=bets_won,
            bets_lost=bets_lost,
            bets_void=bets_void,
            total_staked=total_staked,
            total_returned=total_returned,
            net_profit=net_profit,
            roi_pct=roi_pct,
        )

    # --- Private ---

    def _record(
        self, change_amount: float, reason: BankrollReason,
        related_bet_id: int | None = None,
    ) -> BankrollSnapshot:
        """Append a snapshot. Append-only — never updated."""
        new_balance = self.get_current_balance() + change_amount
        snapshot = BankrollSnapshot(
            balance=new_balance,
            change_amount=change_amount,
            reason=reason.value,
            related_bet_id=related_bet_id,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(snapshot)
        self._session.commit()
        return snapshot
