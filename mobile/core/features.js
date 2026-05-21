// Port of backend/core/features/* — pure functions, no DB, no fetch.
// Same outputs as the Python so prediction numbers match exactly.

// Form score = (wins*3 + draws*1) / (played*3) * 100 — range [0, 100].
// Only counts matches with both goals populated.
export function computeForm(matches, teamId) {
  let wins = 0, draws = 0, losses = 0;

  for (const m of matches) {
    if (m.home_goals == null || m.away_goals == null) continue;
    const isHome = m.home_team_id === teamId;
    const isAway = m.away_team_id === teamId;
    if (!isHome && !isAway) continue;

    const my = isHome ? m.home_goals : m.away_goals;
    const op = isHome ? m.away_goals : m.home_goals;
    if (my > op) wins++;
    else if (my < op) losses++;
    else draws++;
  }

  const played = wins + draws + losses;
  if (played === 0) return { wins: 0, draws: 0, losses: 0, form_score: 0.0 };

  const points = wins * 3 + draws;
  return { wins, draws, losses, form_score: (points / (played * 3)) * 100 };
}

function mean(values) {
  return values.length === 0 ? null : values.reduce((a, b) => a + b, 0) / values.length;
}

export function avgXgFor(matches, teamId) {
  const values = [];
  for (const m of matches) {
    if (m.home_team_id === teamId && m.home_xg != null) values.push(m.home_xg);
    else if (m.away_team_id === teamId && m.away_xg != null) values.push(m.away_xg);
  }
  return mean(values);
}

export function avgXgAgainst(matches, teamId) {
  const values = [];
  for (const m of matches) {
    if (m.home_team_id === teamId && m.away_xg != null) values.push(m.away_xg);
    else if (m.away_team_id === teamId && m.home_xg != null) values.push(m.home_xg);
  }
  return mean(values);
}

// Generic average for any home/away stat pair (possession, shots_on_target, corners).
export function avgStat(matches, teamId, homeAttr, awayAttr) {
  const values = [];
  for (const m of matches) {
    let val = null;
    if (m.home_team_id === teamId) val = m[homeAttr];
    else if (m.away_team_id === teamId) val = m[awayAttr];
    if (val != null) values.push(Number(val));
  }
  return mean(values);
}

// TeamFeatures — same shape as backend/core/types.py.
export function extractTeamFeatures(matches, teamId) {
  const { wins, draws, losses, form_score } = computeForm(matches, teamId);
  const played = wins + draws + losses;

  const gf = [], ga = [];
  for (const m of matches) {
    if (m.home_goals == null || m.away_goals == null) continue;
    if (m.home_team_id === teamId) {
      gf.push(m.home_goals);
      ga.push(m.away_goals);
    } else if (m.away_team_id === teamId) {
      gf.push(m.away_goals);
      ga.push(m.home_goals);
    }
  }

  return {
    team_id: teamId,
    matches_analyzed: played,
    wins, draws, losses, form_score,
    avg_goals_for: gf.length ? gf.reduce((a, b) => a + b, 0) / gf.length : 0.0,
    avg_goals_against: ga.length ? ga.reduce((a, b) => a + b, 0) / ga.length : 0.0,
    avg_xg_for: avgXgFor(matches, teamId),
    avg_xg_against: avgXgAgainst(matches, teamId),
    avg_possession: avgStat(matches, teamId, 'home_possession', 'away_possession'),
    avg_shots_on_target: avgStat(matches, teamId, 'home_shots_on_target', 'away_shots_on_target'),
    avg_corners: avgStat(matches, teamId, 'home_corners', 'away_corners'),
  };
}
