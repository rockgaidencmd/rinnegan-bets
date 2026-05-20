"""Tests for feature extractors.

Uses SimpleNamespace as lightweight mock — satisfies MatchData protocol
without needing ORM or DB.
"""

from types import SimpleNamespace

import pytest

from core.features.extractor import extract_team_features
from core.features.form import compute_form
from core.features.xg import avg_stat, avg_xg_against, avg_xg_for


def _match(home_id, away_id, hg, ag, **stats):
    """Build a mock match with sensible defaults."""
    defaults = {
        "home_xg": None, "away_xg": None,
        "home_possession": None, "away_possession": None,
        "home_shots_on_target": None, "away_shots_on_target": None,
        "home_corners": None, "away_corners": None,
    }
    defaults.update(stats)
    return SimpleNamespace(
        home_team_id=home_id, away_team_id=away_id,
        home_goals=hg, away_goals=ag,
        **defaults,
    )


BARCELONA = 100
REAL_MADRID = 200
UNKNOWN_TEAM = 999


# --- compute_form ---

class TestComputeForm:

    def test_empty_list_returns_zeros(self):
        assert compute_form([], BARCELONA) == (0, 0, 0, 0.0)

    def test_team_not_in_any_match_returns_zeros(self):
        matches = [_match(REAL_MADRID, 300, 2, 1)]
        assert compute_form(matches, BARCELONA) == (0, 0, 0, 0.0)

    def test_three_wins_at_home_full_form_score(self):
        matches = [
            _match(BARCELONA, 1, 3, 0),
            _match(BARCELONA, 2, 2, 1),
            _match(BARCELONA, 3, 1, 0),
        ]
        wins, draws, losses, score = compute_form(matches, BARCELONA)
        assert wins == 3
        assert draws == 0
        assert losses == 0
        assert score == pytest.approx(100.0)

    def test_mixed_results_partial_form_score(self):
        matches = [
            _match(BARCELONA, 1, 3, 0),    # W
            _match(BARCELONA, 2, 1, 1),    # D
            _match(3, BARCELONA, 2, 0),    # L (Barcelona is away, lost 0-2)
        ]
        wins, draws, losses, score = compute_form(matches, BARCELONA)
        assert wins == 1
        assert draws == 1
        assert losses == 1
        # points = 3+1+0 = 4 / 9 max = 44.4%
        assert score == pytest.approx(44.44, abs=0.1)

    def test_handles_team_as_home_or_away(self):
        matches = [
            _match(BARCELONA, 1, 2, 0),    # W at home
            _match(2, BARCELONA, 0, 3),    # W away
        ]
        wins, _, _, score = compute_form(matches, BARCELONA)
        assert wins == 2
        assert score == pytest.approx(100.0)

    def test_skips_matches_without_goals(self):
        matches = [
            _match(BARCELONA, 1, None, None),  # not played yet
            _match(BARCELONA, 2, 2, 0),
        ]
        wins, _, _, _ = compute_form(matches, BARCELONA)
        assert wins == 1


# --- xG helpers ---

class TestXG:

    def test_avg_xg_for_returns_none_when_no_data(self):
        matches = [_match(BARCELONA, 1, 2, 0)]  # no xG provided
        assert avg_xg_for(matches, BARCELONA) is None

    def test_avg_xg_for_averages_across_home_and_away(self):
        matches = [
            _match(BARCELONA, 1, 2, 0, home_xg=2.0),  # home → use home_xg
            _match(2, BARCELONA, 1, 1, away_xg=1.0),  # away → use away_xg
        ]
        assert avg_xg_for(matches, BARCELONA) == pytest.approx(1.5)

    def test_avg_xg_against_uses_opponent_xg(self):
        matches = [
            _match(BARCELONA, 1, 2, 0, home_xg=2.0, away_xg=0.5),
            _match(2, BARCELONA, 1, 1, home_xg=1.5, away_xg=1.0),
        ]
        # Barca conceded away_xg(0.5) at home, then home_xg(1.5) away
        assert avg_xg_against(matches, BARCELONA) == pytest.approx(1.0)

    def test_avg_stat_generic_works_for_possession(self):
        matches = [
            _match(BARCELONA, 1, 0, 0, home_possession=60.0),
            _match(2, BARCELONA, 0, 0, away_possession=70.0),
        ]
        assert avg_stat(matches, BARCELONA, "home_possession", "away_possession") == pytest.approx(65.0)


# --- extract_team_features ---

class TestExtractTeamFeatures:

    def test_empty_matches_returns_zero_features(self):
        f = extract_team_features([], BARCELONA)
        assert f.team_id == BARCELONA
        assert f.matches_analyzed == 0
        assert f.form_score == 0.0
        assert f.avg_xg_for is None
        assert f.avg_possession is None

    def test_full_features_extracted_from_real_data(self):
        matches = [
            _match(BARCELONA, 1, 3, 1, home_xg=2.5, away_xg=0.8,
                   home_possession=65.0, away_possession=35.0,
                   home_shots_on_target=7, away_shots_on_target=3,
                   home_corners=8, away_corners=2),
            _match(2, BARCELONA, 0, 2, home_xg=0.6, away_xg=1.9,
                   home_possession=40.0, away_possession=60.0,
                   home_shots_on_target=2, away_shots_on_target=6,
                   home_corners=3, away_corners=7),
        ]
        f = extract_team_features(matches, BARCELONA)
        assert f.matches_analyzed == 2
        assert f.wins == 2
        assert f.form_score == pytest.approx(100.0)
        assert f.avg_goals_for == pytest.approx(2.5)   # (3+2)/2
        assert f.avg_goals_against == pytest.approx(0.5)  # (1+0)/2
        assert f.avg_xg_for == pytest.approx(2.2)      # (2.5+1.9)/2
        assert f.avg_xg_against == pytest.approx(0.7)  # (0.8+0.6)/2
        assert f.avg_possession == pytest.approx(62.5)
        assert f.avg_shots_on_target == pytest.approx(6.5)
        assert f.avg_corners == pytest.approx(7.5)

    def test_handles_partial_xg_data(self):
        """Some matches have xG, others don't — should average only available."""
        matches = [
            _match(BARCELONA, 1, 1, 0, home_xg=1.5),
            _match(BARCELONA, 2, 2, 1),  # no xG
            _match(BARCELONA, 3, 0, 0, home_xg=0.5),
        ]
        f = extract_team_features(matches, BARCELONA)
        assert f.avg_xg_for == pytest.approx(1.0)  # (1.5 + 0.5) / 2
        assert f.matches_analyzed == 3  # all 3 played
