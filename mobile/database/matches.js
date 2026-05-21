// listMatches: backend's MatchListResponse — { matches, total, total_available, offset }.
// total = page size returned now, total_available = full count matching
// the filter (used by the "Cargar más" pagination).
export function listMatches(db, { league, team_id, limit = 25, offset = 0 } = {}) {
  const conditions = ['m.home_goals IS NOT NULL'];
  const params = [];
  if (league) {
    conditions.push('m.league = ?');
    params.push(league);
  }
  if (team_id) {
    conditions.push('(m.home_team_id = ? OR m.away_team_id = ?)');
    params.push(team_id, team_id);
  }
  const where = conditions.join(' AND ');

  const totalAvailable = db.getFirstSync(
    `SELECT COUNT(*) AS n FROM matches m WHERE ${where}`,
    params,
  ).n;

  const rows = db.getAllSync(
    `SELECT m.id, m.league, m.match_date,
            m.home_team_id, ht.name AS home_team_name,
            m.away_team_id, at.name AS away_team_name,
            m.home_goals, m.away_goals, m.result, m.home_xg, m.away_xg
     FROM matches m
     JOIN teams ht ON ht.id = m.home_team_id
     JOIN teams at ON at.id = m.away_team_id
     WHERE ${where}
     ORDER BY m.match_date DESC, m.id DESC
     LIMIT ? OFFSET ?`,
    [...params, limit, offset],
  );

  return {
    matches: rows,
    total: rows.length,
    total_available: totalAvailable,
    offset,
  };
}

// Used by core/predict — last N matches a team played, with stats.
export function getLastMatchesForTeam(db, teamId, limit = 10) {
  return db.getAllSync(
    `SELECT * FROM matches
     WHERE (home_team_id = ? OR away_team_id = ?)
       AND home_goals IS NOT NULL
     ORDER BY match_date DESC
     LIMIT ?`,
    [teamId, teamId, limit],
  );
}
