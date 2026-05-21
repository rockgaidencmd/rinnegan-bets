"""Bankroll schemas — Request/Response DTOs."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from api.schemas._types import UtcDatetime


# --- Requests ---

class DepositRequest(BaseModel):
    amount: float = Field(gt=0)


class WithdrawRequest(BaseModel):
    amount: float = Field(gt=0)


class PlaceBetRequest(BaseModel):
    prediction_id: int = Field(gt=0)
    quota: float = Field(gt=1.0)
    stake: float = Field(gt=0)


class SettleBetRequest(BaseModel):
    outcome: Literal["won", "lost", "void"]


# --- Responses ---

class BalanceResponse(BaseModel):
    current: float
    available: float
    pending_commitment: float


class SnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    balance: float
    change_amount: float
    reason: str
    related_bet_id: int | None = None
    created_at: UtcDatetime


class BetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prediction_id: int
    quota_used: float
    stake_amount: float
    placed_at: UtcDatetime
    outcome: str
    payout_amount: float | None = None
    settled_at: UtcDatetime | None = None


class SettleBetResponse(BaseModel):
    bet: BetResponse
    snapshot: SnapshotResponse | None = None


class RoiResponse(BaseModel):
    period_start: UtcDatetime | None = None
    period_end: UtcDatetime | None = None
    bets_settled: int
    bets_won: int
    bets_lost: int
    bets_void: int
    total_staked: float
    total_returned: float
    net_profit: float
    roi_pct: float


class HistoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    balance: float
    change_amount: float
    reason: str
    related_bet_id: int | None = None
    created_at: UtcDatetime


class HistoryResponse(BaseModel):
    items: list[HistoryItemResponse]
    total: int
