import { useEffect, useState } from 'react';
import { api } from '../utils/api.js';


/**
 * useTeamData — single source of truth for "load a team's stats + recent matches".
 *
 * Replaces the duplicated fetch logic that lived in TeamStatsPreview and
 * TeamDetailModal. Both screens now use this hook and pick what they render.
 *
 * Parallel fetch via Promise.all + ignore flag for safe unmount/refetch.
 */
export function useTeamData(teamId, { matchesLimit = 10 } = {}) {
  const [stats, setStats] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!teamId) {
      setStats(null);
      setMatches([]);
      return;
    }

    let ignore = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const [statsData, matchesData] = await Promise.all([
          api.getTeamStats(teamId, matchesLimit),
          api.listMatches({ team_id: teamId, limit: matchesLimit }),
        ]);
        if (!ignore) {
          setStats(statsData);
          setMatches(matchesData.matches);
        }
      } catch (err) {
        if (!ignore) {
          setError(err);
          setStats(null);
          setMatches([]);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    })();

    return () => { ignore = true; };
  }, [teamId, matchesLimit]);

  return { stats, matches, loading, error };
}
