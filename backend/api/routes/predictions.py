"""Prediction endpoint — the core "should I bet?" decision."""

from fastapi import APIRouter
from sqlalchemy import or_, select

from api.deps import DbSession
from api.schemas.predictions import PredictRequest, PredictResponse
from core.features.extractor import extract_team_features
from core.models.factory import get_model_for_league
from core.types import MatchContext
from data.team_search import find_teams_by_name, resolve_matchup
from db.models import Match


router = APIRouter(prefix="/api/predictions", tags=["predictions"])


def _get_last_matches(db, team_id: int, limit: int = 10) -> list[Match]:
    return db.execute(
        select(Match)
        .where(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))
        .where(Match.home_goals.is_not(None))
        .order_by(Match.match_date.desc())
        .limit(limit)
    ).scalars().all()


@router.post("", response_model=PredictResponse)
def predict_match(body: PredictRequest, db: DbSession) -> PredictResponse:
    """Predict the outcome of a hypothetical match given odds and stake.

    Currently predicts only "Victoria Local" (1X2 → 1) market.
    Other markets (over/under, BTTS) require dedicated models.
    """
    home_candidates = find_teams_by_name(db, body.home_team)
    away_candidates = find_teams_by_name(db, body.away_team)
    home, away, league = resolve_matchup(home_candidates, away_candidates, body.force)

    home_matches = _get_last_matches(db, home.id)
    away_matches = _get_last_matches(db, away.id)
    home_features = extract_team_features(home_matches, home.id)
    away_features = extract_team_features(away_matches, away.id)

    context = MatchContext(
        importance=body.importance,
        home_key_absences=body.home_key_absences,
        away_key_absences=body.away_key_absences,
    )
    model = get_model_for_league(league)
    prediction = model.predict(home_features, away_features, context, body.quota, body.stake)

    return PredictResponse(
        home_team=home.name,
        away_team=away.name,
        league=league,
        model_version=prediction.model_version,
        my_prob=float(prediction.my_prob),
        implied_prob=float(prediction.implied_prob),
        edge=float(prediction.my_prob - prediction.implied_prob),
        quota=float(prediction.quota),
        stake=float(prediction.stake),
        ev=float(prediction.ev),
        kelly=float(prediction.kelly),
        pre_score=prediction.pre_score,
        verdict=prediction.verdict.verdict,
        verdict_reason=prediction.verdict.reason,
        reasoning=prediction.reasoning,
    )
