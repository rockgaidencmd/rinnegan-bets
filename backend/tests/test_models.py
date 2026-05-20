"""Tests for prediction models (Europe + Ecuador).

Validate:
- Weights sum to 1.0
- Pre-score in [0, 100]
- Probabilities clamped to [0.05, 0.95]
- Verdicts respond correctly to scenarios
- Model factory selects correctly
"""

import pytest

from core.models.ecuador import EcuadorModel
from core.models.europe import EuropeModel
from core.models.factory import get_model_for_league
from core.types import (
    Apostar,
    Esperar,
    MatchContext,
    NoApostar,
    Prediction,
    TeamFeatures,
)


def _features(
    team_id: int, form: float = 50.0,
    xg_for: float | None = 1.5, xg_against: float | None = 1.5,
    goals_for: float = 1.5, goals_against: float = 1.5,
    possession: float | None = 50.0,
    shots: float | None = 4.0,
) -> TeamFeatures:
    """Build a TeamFeatures with sensible defaults."""
    return TeamFeatures(
        team_id=team_id,
        matches_analyzed=5,
        wins=2, draws=2, losses=1,
        form_score=form,
        avg_goals_for=goals_for,
        avg_goals_against=goals_against,
        avg_xg_for=xg_for,
        avg_xg_against=xg_against,
        avg_possession=possession,
        avg_shots_on_target=shots,
        avg_corners=5.0,
    )


# --- EuropeModel ---

class TestEuropeModel:

    def test_weights_sum_to_one(self):
        model = EuropeModel()
        assert abs(sum(model.weights.values()) - 1.0) < 0.001

    def test_invalid_weights_raise(self):
        bad_weights = {"xg_diff": 0.5, "form_diff": 0.5, "extra": 0.5}  # sums to 1.5
        with pytest.raises(ValueError, match="must sum to 1.0"):
            EuropeModel(weights=bad_weights)

    def test_pre_score_in_range(self):
        model = EuropeModel()
        result = model.predict(
            _features(1, form=80, xg_for=2.0, xg_against=0.8),
            _features(2, form=30, xg_for=0.9, xg_against=2.1),
            MatchContext(),
            quota=2.0, stake=10.0,
        )
        assert 0 <= result.pre_score <= 100

    def test_strong_home_vs_weak_away_gives_high_pre_score(self):
        """A clearly stronger home team should produce pre_score >> 50."""
        model = EuropeModel()
        result = model.predict(
            _features(1, form=90, xg_for=2.5, xg_against=0.5, goals_for=3.0),
            _features(2, form=20, xg_for=0.8, xg_against=2.5, goals_for=0.8),
            MatchContext(),
            quota=2.0, stake=10.0,
        )
        assert result.pre_score > 60

    def test_evenly_matched_teams_centered_pre_score(self):
        model = EuropeModel()
        # Identical features → only home_advantage tilts it
        feat = _features(0)
        result = model.predict(
            _features(1, form=50, xg_for=1.5, xg_against=1.5),
            _features(2, form=50, xg_for=1.5, xg_against=1.5),
            MatchContext(),
            quota=2.0, stake=10.0,
        )
        # Home advantage adds tilt, so pre_score should be > 50 but not extreme
        assert 50 < result.pre_score < 75

    def test_value_bet_yields_apostar(self):
        """Strong team at long odds — should recommend bet."""
        model = EuropeModel()
        result = model.predict(
            _features(1, form=80, xg_for=2.2, xg_against=0.7, goals_for=2.4),
            _features(2, form=30, xg_for=0.8, xg_against=2.2, goals_for=0.7),
            MatchContext(importance="clasif"),
            quota=2.50,   # market underestimates strong team
            stake=10.0,
        )
        assert isinstance(result.verdict, Apostar)
        assert result.ev > 0
        assert result.kelly > 0

    def test_overpriced_match_yields_no_apostar(self):
        """Weak team at short odds — no edge."""
        model = EuropeModel()
        result = model.predict(
            _features(1, form=30, xg_for=0.8, xg_against=2.0),
            _features(2, form=80, xg_for=2.2, xg_against=0.7),
            MatchContext(),
            quota=1.30,   # huge favorite, low odds
            stake=10.0,
        )
        assert isinstance(result.verdict, NoApostar)

    def test_my_prob_in_safe_range(self):
        """Even extreme cases should clamp to [0.05, 0.95]."""
        model = EuropeModel()
        result = model.predict(
            _features(1, form=100, xg_for=5.0, xg_against=0.1),
            _features(2, form=0, xg_for=0.1, xg_against=5.0),
            MatchContext(importance="final"),
            quota=1.10, stake=10.0,
        )
        assert 0.05 <= result.my_prob <= 0.95

    def test_reasoning_includes_components(self):
        model = EuropeModel()
        result = model.predict(
            _features(1), _features(2), MatchContext(),
            quota=2.0, stake=10.0,
        )
        assert "components" in result.reasoning
        assert "weights" in result.reasoning
        # All weight keys should appear in components
        assert set(result.reasoning["components"].keys()) == set(model.weights.keys())


# --- EcuadorModel ---

class TestEcuadorModel:

    def test_weights_sum_to_one(self):
        model = EcuadorModel()
        assert abs(sum(model.weights.values()) - 1.0) < 0.001

    def test_works_without_xg_data(self):
        """Ecuador model must produce a prediction even when xG is None."""
        model = EcuadorModel()
        result = model.predict(
            _features(1, xg_for=None, xg_against=None, shots=6.0),
            _features(2, xg_for=None, xg_against=None, shots=3.0),
            MatchContext(),
            quota=2.0, stake=10.0,
        )
        assert isinstance(result, Prediction)
        assert 0 <= result.pre_score <= 100

    def test_more_shots_on_target_increases_score(self):
        """Higher shots-on-target avg should favor that team."""
        model = EcuadorModel()
        result_strong = model.predict(
            _features(1, xg_for=None, shots=8.0, form=70),
            _features(2, xg_for=None, shots=2.0, form=30),
            MatchContext(),
            quota=2.0, stake=10.0,
        )
        result_weak = model.predict(
            _features(1, xg_for=None, shots=2.0, form=30),
            _features(2, xg_for=None, shots=8.0, form=70),
            MatchContext(),
            quota=2.0, stake=10.0,
        )
        assert result_strong.pre_score > result_weak.pre_score

    def test_home_advantage_stronger_than_europe(self):
        """Ecuador home factor should give bigger boost than Europe's."""
        ecu = EcuadorModel()
        eur = EuropeModel()
        identical = _features(0)
        ecu_result = ecu.predict(
            _features(1), _features(2), MatchContext(),
            quota=2.0, stake=10.0,
        )
        eur_result = eur.predict(
            _features(1), _features(2), MatchContext(),
            quota=2.0, stake=10.0,
        )
        assert ecu_result.pre_score >= eur_result.pre_score


# --- Factory ---

class TestModelFactory:

    @pytest.mark.parametrize("league", ["PL", "PD", "BL1", "SA", "FL1", "CL"])
    def test_europe_leagues_get_europe_model(self, league):
        model = get_model_for_league(league)
        assert isinstance(model, EuropeModel)

    @pytest.mark.parametrize("league", ["EC1", "LIB"])
    def test_ecuador_style_leagues_get_ecuador_model(self, league):
        model = get_model_for_league(league)
        assert isinstance(model, EcuadorModel)

    def test_unknown_league_raises(self):
        with pytest.raises(ValueError, match="No model configured"):
            get_model_for_league("MLS")
