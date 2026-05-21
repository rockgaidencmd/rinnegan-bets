import { extractTeamFeatures } from '../core/features';

// searchTeams: backend's TeamSearchResponse shape — { query, results, count }.
// LIKE search on name + slug, deduped by sofascore_id (keeping the
// lowest team.id when the same team appears across multiple leagues,
// e.g. Real Madrid in both PD and CL).
export function searchTeams(db, q, limit = 10) {
  const term = `%${q.toLowerCase()}%`;
  const rows = db.getAllSync(
    `SELECT * FROM teams
     WHERE LOWER(name) LIKE ? OR LOWER(slug) LIKE ?
     ORDER BY id ASC
     LIMIT ?`,
    [term, term, limit * 3],
  );

  const seen = new Set();
  const results = [];
  for (const r of rows) {
    if (r.sofascore_id != null) {
      if (seen.has(r.sofascore_id)) continue;
      seen.add(r.sofascore_id);
    }
    results.push(r);
    if (results.length >= limit) break;
  }

  return { query: q, results, count: results.length };
}

// Backend returns a raw array (response_model=list[TeamResponse]).
export function getTeamsByLeague(db, code) {
  return db.getAllSync(
    'SELECT * FROM teams WHERE league = ? ORDER BY name COLLATE NOCASE ASC',
    [code],
  );
}

// getTeamStats: backend's TeamStatsResponse — reads last 10 played
// matches and delegates the math to core/features.extractTeamFeatures
// so the formulas live in one place.
export function getTeamStats(db, teamId, lastN = 10) {
  const team = db.getFirstSync(
    'SELECT id, name FROM teams WHERE id = ?',
    [teamId],
  );
  if (!team) {
    throw new Error(`Team ${teamId} not found`);
  }

  const matches = db.getAllSync(
    `SELECT * FROM matches
     WHERE (home_team_id = ? OR away_team_id = ?)
       AND home_goals IS NOT NULL
     ORDER BY match_date DESC
     LIMIT ?`,
    [teamId, teamId, lastN],
  );

  const features = extractTeamFeatures(matches, teamId);

  return {
    team_id: team.id,
    team_name: team.name,
    matches_analyzed: features.matches_analyzed,
    wins: features.wins,
    draws: features.draws,
    losses: features.losses,
    form_score: features.form_score,
    avg_goals_for: features.avg_goals_for,
    avg_goals_against: features.avg_goals_against,
    avg_xg_for: features.avg_xg_for,
    avg_xg_against: features.avg_xg_against,
    avg_possession: features.avg_possession,
    avg_shots_on_target: features.avg_shots_on_target,
    avg_corners: features.avg_corners,
  };
}
