import { LEAGUES } from '../core/leagues';

// Same shape as backend /api/leagues: { leagues: [...], total }.
// Returns the full static catalog with team_count + match_count joined
// from the local DB (zeros when a league has nothing seeded).
export function listLeagues(db) {
  const teamCounts = Object.fromEntries(
    db.getAllSync(
      'SELECT league, COUNT(*) AS n FROM teams GROUP BY league',
    ).map((r) => [r.league, r.n]),
  );
  const matchCounts = Object.fromEntries(
    db.getAllSync(
      `SELECT league, COUNT(*) AS n FROM matches
       WHERE home_goals IS NOT NULL GROUP BY league`,
    ).map((r) => [r.league, r.n]),
  );

  const leagues = Object.values(LEAGUES).map((info) => ({
    code: info.code,
    name: info.name,
    country: info.country,
    team_count: teamCounts[info.code] || 0,
    match_count: matchCounts[info.code] || 0,
  }));

  return { leagues, total: leagues.length };
}
