// listFixtures: backend's FixtureListResponse — { league, fixtures, total }.
// Standalone mode reads from the bundled snapshot in the fixtures
// table — there's no live fetch yet (see README "refresh strategy").
export function listFixtures(db, { league, days = 7, limit = 20 } = {}) {
  if (!league) {
    return { league: '', fixtures: [], total: 0 };
  }

  // SQLite's datetime() works on ISO-8601 strings and that's what the
  // backend writes, so this comparison is well-defined.
  const upper = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toISOString();
  const rows = db.getAllSync(
    `SELECT league, match_date,
            home_team_id, home_team_name,
            away_team_id, away_team_name
     FROM fixtures
     WHERE league = ?
       AND match_date <= ?
       AND match_date >= datetime('now', '-1 day')
     ORDER BY match_date ASC
     LIMIT ?`,
    [league, upper, limit],
  );

  return { league, fixtures: rows, total: rows.length };
}
