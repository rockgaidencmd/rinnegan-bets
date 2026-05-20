"""Combine all feature extractors into TeamFeatures."""

from core.features import MatchData
from core.features.form import compute_form
from core.features.xg import avg_stat, avg_xg_against, avg_xg_for
from core.types import TeamFeatures


def extract_team_features(matches: list[MatchData], team_id: int) -> TeamFeatures:
    """Build a complete TeamFeatures from a team's recent matches.

    Pure function: same input → same output. No DB, no HTTP.
    Caller is responsible for fetching the right matches (e.g., last 5).
    """
    wins, draws, losses, form_score = compute_form(matches, team_id)
    played = wins + draws + losses

    # Goals scored/conceded averages
    gf_values, ga_values = [], []
    for m in matches:
        if m.home_goals is None or m.away_goals is None:
            continue
        if m.home_team_id == team_id:
            gf_values.append(m.home_goals)
            ga_values.append(m.away_goals)
        elif m.away_team_id == team_id:
            gf_values.append(m.away_goals)
            ga_values.append(m.home_goals)

    return TeamFeatures(
        team_id=team_id,
        matches_analyzed=played,
        wins=wins,
        draws=draws,
        losses=losses,
        form_score=form_score,
        avg_goals_for=sum(gf_values) / len(gf_values) if gf_values else 0.0,
        avg_goals_against=sum(ga_values) / len(ga_values) if ga_values else 0.0,
        avg_xg_for=avg_xg_for(matches, team_id),
        avg_xg_against=avg_xg_against(matches, team_id),
        avg_possession=avg_stat(matches, team_id, "home_possession", "away_possession"),
        avg_shots_on_target=avg_stat(matches, team_id, "home_shots_on_target", "away_shots_on_target"),
        avg_corners=avg_stat(matches, team_id, "home_corners", "away_corners"),
    )
