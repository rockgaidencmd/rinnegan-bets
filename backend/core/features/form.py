"""Form score: how many points the team has earned recently.

Form score formula:
    (wins * 3 + draws * 1) / (matches * 3) * 100
    → 100 = perfect run, 0 = no points won
"""

from core.features import MatchData


def compute_form(matches: list[MatchData], team_id: int) -> tuple[int, int, int, float]:
    """Count wins/draws/losses for a team and compute form_score (0-100).

    Returns (wins, draws, losses, form_score). Empty list → (0, 0, 0, 0.0).
    Only counts matches with both goal values populated (i.e., finished).
    """
    wins = draws = losses = 0

    for match in matches:
        if match.home_goals is None or match.away_goals is None:
            continue

        is_home = match.home_team_id == team_id
        is_away = match.away_team_id == team_id
        if not (is_home or is_away):
            continue

        team_goals = match.home_goals if is_home else match.away_goals
        opp_goals = match.away_goals if is_home else match.home_goals

        if team_goals > opp_goals:
            wins += 1
        elif team_goals < opp_goals:
            losses += 1
        else:
            draws += 1

    played = wins + draws + losses
    if played == 0:
        return 0, 0, 0, 0.0

    points = wins * 3 + draws * 1
    form_score = (points / (played * 3)) * 100
    return wins, draws, losses, form_score
