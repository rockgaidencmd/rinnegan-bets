"""Bankroll endpoints — balance, deposit/withdraw, place bets, settle, ROI."""

from fastapi import APIRouter, Query
from sqlalchemy import select

from api.deps import BankrollDep, DbSession
from api.schemas.bankroll import (
    BalanceResponse,
    BetResponse,
    DepositRequest,
    HistoryItemResponse,
    HistoryResponse,
    PlaceBetRequest,
    RoiResponse,
    SettleBetRequest,
    SettleBetResponse,
    SnapshotResponse,
    WithdrawRequest,
)
from db.enums import BetOutcome
from db.models import BankrollSnapshot


router = APIRouter(prefix="/api/bankroll", tags=["bankroll"])


@router.get("", response_model=BalanceResponse)
def get_balance(tracker: BankrollDep) -> BalanceResponse:
    """Current bankroll state — total, committed in pending bets, available."""
    return BalanceResponse(
        current=tracker.get_current_balance(),
        available=tracker.get_available_balance(),
        pending_commitment=tracker.get_pending_commitment(),
    )


@router.post("/deposit", response_model=SnapshotResponse, status_code=201)
def deposit(body: DepositRequest, tracker: BankrollDep) -> SnapshotResponse:
    """Add funds to the bankroll."""
    snapshot = tracker.deposit(body.amount)
    return SnapshotResponse.model_validate(snapshot)


@router.post("/withdraw", response_model=SnapshotResponse, status_code=201)
def withdraw(body: WithdrawRequest, tracker: BankrollDep) -> SnapshotResponse:
    """Remove funds from the bankroll. Fails if committed capital would go negative."""
    snapshot = tracker.withdraw(body.amount)
    return SnapshotResponse.model_validate(snapshot)


@router.post("/bets", response_model=BetResponse, status_code=201)
def place_bet(body: PlaceBetRequest, tracker: BankrollDep) -> BetResponse:
    """Place a bet against a prediction. Locks stake until settle."""
    bet = tracker.place_bet(body.prediction_id, body.quota, body.stake)
    return BetResponse.model_validate(bet)


@router.post("/bets/{bet_id}/settle", response_model=SettleBetResponse)
def settle_bet(
    bet_id: int, body: SettleBetRequest, tracker: BankrollDep,
) -> SettleBetResponse:
    """Settle a pending bet as won, lost, or void. Updates bankroll accordingly."""
    bet, snapshot = tracker.settle_bet(bet_id, BetOutcome(body.outcome))
    return SettleBetResponse(
        bet=BetResponse.model_validate(bet),
        snapshot=SnapshotResponse.model_validate(snapshot) if snapshot else None,
    )


@router.get("/roi", response_model=RoiResponse)
def get_roi(tracker: BankrollDep) -> RoiResponse:
    """Win rate + net profit + ROI across all settled bets."""
    report = tracker.compute_roi()
    return RoiResponse(**report.__dict__)


@router.get("/history", response_model=HistoryResponse)
def get_history(db: DbSession, limit: int = Query(20, ge=1, le=200)) -> HistoryResponse:
    """Recent bankroll movements (deposits, withdrawals, bet outcomes)."""
    rows = db.execute(
        select(BankrollSnapshot)
        .order_by(BankrollSnapshot.created_at.desc())
        .limit(limit)
    ).scalars().all()
    return HistoryResponse(
        items=[HistoryItemResponse.model_validate(r) for r in rows],
        total=len(rows),
    )
