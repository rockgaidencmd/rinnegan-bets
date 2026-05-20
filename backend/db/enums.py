"""String-based enums stored as VARCHAR + CHECK constraint in SQLite.

Using StrEnum instead of sa.Enum to keep migrations clean
(adding a new value = drop+create constraint, not full table rebuild).
"""

from enum import StrEnum


class MatchResult(StrEnum):
    HOME_WIN = "H"
    DRAW = "D"
    AWAY_WIN = "A"


class DataSource(StrEnum):
    FOOTBALL_DATA = "football_data"
    SOFASCORE = "sofascore"
    MANUAL = "manual"


class League(StrEnum):
    """Supported leagues. Add new ones as needed."""
    PREMIER_LEAGUE = "PL"
    LA_LIGA = "PD"
    BUNDESLIGA = "BL1"
    SERIE_A = "SA"
    LIGUE_1 = "FL1"
    CHAMPIONS_LEAGUE = "CL"
    COPA_LIBERTADORES = "LIB"
    LIGA_PRO_ECUADOR = "EC1"
    OTHER = "OTHER"


class PredictionVerdict(StrEnum):
    APOSTAR = "apostar"
    ESPERAR = "esperar"
    NO_APOSTAR = "no_apostar"


class BetOutcome(StrEnum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    VOID = "void"  # postponed match, etc.


class BankrollReason(StrEnum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    BET_WON = "bet_won"
    BET_LOST = "bet_lost"
    BET_VOID = "bet_void"
    ADJUSTMENT = "adjustment"


def values(enum_cls: type[StrEnum]) -> tuple[str, ...]:
    """Return all values of an enum as a tuple — for CHECK constraints."""
    return tuple(member.value for member in enum_cls)
