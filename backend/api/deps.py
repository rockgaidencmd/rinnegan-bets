"""FastAPI dependencies — dependency injection helpers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from core.bankroll.tracker import BankrollTracker
from db.database import get_db


DbSession = Annotated[Session, Depends(get_db)]


def get_bankroll_tracker(db: DbSession) -> BankrollTracker:
    """BankrollTracker bound to the request's DB session."""
    return BankrollTracker(db)


BankrollDep = Annotated[BankrollTracker, Depends(get_bankroll_tracker)]
