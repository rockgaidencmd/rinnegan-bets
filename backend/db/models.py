"""ORM models for Rinnegan Bets.

All entities use TimestampMixin. Enums stored as VARCHAR + CHECK constraint.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.enums import (
    BankrollReason,
    BetOutcome,
    DataSource,
    League,
    MatchResult,
    PredictionVerdict,
    values,
)
from db.mixins import TimestampMixin


class Team(Base, TimestampMixin):
    """A football team."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    league: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # External IDs for cross-referencing API responses
    football_data_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    sofascore_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint("slug", "league", name="uq_teams_slug_league"),
        CheckConstraint(f"league IN {values(League)}", name="ck_teams_league"),
        Index("ix_teams_name", "name"),
    )


class Match(Base, TimestampMixin):
    """A historical match with stats."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    league: Mapped[str] = mapped_column(String(20), nullable=False)
    match_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Results
    home_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[str | None] = mapped_column(String(1), nullable=True)  # H/D/A

    # Stats — nullable because some sources don't provide them all
    home_xg: Mapped[float | None] = mapped_column(Float, nullable=True)
    away_xg: Mapped[float | None] = mapped_column(Float, nullable=True)
    home_possession: Mapped[float | None] = mapped_column(Float, nullable=True)
    away_possession: Mapped[float | None] = mapped_column(Float, nullable=True)
    home_shots_on_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_shots_on_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_corners: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_corners: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_yellow_cards: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_yellow_cards: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Provenance
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    home_team: Mapped["Team"] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship(foreign_keys=[away_team_id])

    __table_args__ = (
        UniqueConstraint(
            "source", "external_id", name="uq_matches_source_external_id"
        ),
        CheckConstraint(f"league IN {values(League)}", name="ck_matches_league"),
        CheckConstraint(f"source IN {values(DataSource)}", name="ck_matches_source"),
        CheckConstraint(
            f"result IN {values(MatchResult)} OR result IS NULL",
            name="ck_matches_result",
        ),
        Index("ix_matches_home_team_date", "home_team_id", "match_date"),
        Index("ix_matches_away_team_date", "away_team_id", "match_date"),
        Index("ix_matches_league_date", "league", "match_date"),
    )


class DataCache(Base):
    """HTTP response cache with TTL.

    No TimestampMixin: uses fetched_at + expires_at instead.
    """

    __tablename__ = "data_cache"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_data_cache_expires_at", "expires_at"),
    )


class Prediction(Base, TimestampMixin):
    """A model prediction. May or may not be turned into a real bet."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    match_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    league: Mapped[str] = mapped_column(String(20), nullable=False)

    # Model identification
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)

    # Scores
    pre_score: Mapped[float] = mapped_column(Float, nullable=False)
    implied_prob: Mapped[float] = mapped_column(Float, nullable=False)
    my_prob: Mapped[float] = mapped_column(Float, nullable=False)

    # Decision
    ev: Mapped[float] = mapped_column(Float, nullable=False)
    kelly_fraction: Mapped[float] = mapped_column(Float, nullable=False)
    quota: Mapped[float] = mapped_column(Float, nullable=False)
    stake: Mapped[float] = mapped_column(Float, nullable=False)
    verdict: Mapped[str] = mapped_column(String(20), nullable=False)

    # Explainability — what features drove this prediction
    reasoning: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        CheckConstraint(f"league IN {values(League)}", name="ck_predictions_league"),
        CheckConstraint(
            f"verdict IN {values(PredictionVerdict)}",
            name="ck_predictions_verdict",
        ),
        CheckConstraint("pre_score >= 0 AND pre_score <= 100", name="ck_predictions_pre_score_range"),
        CheckConstraint("implied_prob >= 0 AND implied_prob <= 100", name="ck_predictions_implied_prob_range"),
        CheckConstraint("my_prob >= 0 AND my_prob <= 100", name="ck_predictions_my_prob_range"),
        CheckConstraint("kelly_fraction >= 0 AND kelly_fraction <= 1", name="ck_predictions_kelly_range"),
        CheckConstraint("quota > 1", name="ck_predictions_quota_positive"),
        CheckConstraint("stake >= 0", name="ck_predictions_stake_positive"),
        Index("ix_predictions_match_date", "match_date"),
    )


class Bet(Base, TimestampMixin):
    """An actual bet placed (subset of predictions)."""

    __tablename__ = "bets"

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("predictions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    quota_used: Mapped[float] = mapped_column(Float, nullable=False)
    stake_amount: Mapped[float] = mapped_column(Float, nullable=False)
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    outcome: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BetOutcome.PENDING.value
    )
    payout_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    prediction: Mapped["Prediction"] = relationship(foreign_keys=[prediction_id])

    __table_args__ = (
        CheckConstraint(f"outcome IN {values(BetOutcome)}", name="ck_bets_outcome"),
        CheckConstraint("quota_used > 1", name="ck_bets_quota_positive"),
        CheckConstraint("stake_amount > 0", name="ck_bets_stake_positive"),
        Index("ix_bets_outcome", "outcome"),
    )


class BankrollSnapshot(Base):
    """Audit trail of bankroll changes. Append-only.

    Current balance = SELECT balance FROM bankroll_snapshots
                      ORDER BY created_at DESC LIMIT 1
    """

    __tablename__ = "bankroll_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    balance: Mapped[float] = mapped_column(Float, nullable=False)
    change_amount: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(String(30), nullable=False)
    related_bet_id: Mapped[int | None] = mapped_column(
        ForeignKey("bets.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        CheckConstraint(f"reason IN {values(BankrollReason)}", name="ck_bankroll_snapshots_reason"),
    )


class ModelPerformance(Base, TimestampMixin):
    """Snapshot of model performance over a time window."""

    __tablename__ = "model_performance"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    predictions_count: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    roi_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    brier_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_model_performance_version_period", "model_version", "period_start"),
        CheckConstraint("predictions_count >= 0", name="ck_model_performance_count_positive"),
        CheckConstraint(
            "correct_count >= 0 AND correct_count <= predictions_count",
            name="ck_model_performance_correct_valid",
        ),
    )
