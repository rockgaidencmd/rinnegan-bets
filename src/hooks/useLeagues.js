import { useEffect, useState } from 'react';
import { api } from '../utils/api.js';


/**
 * useLeagues — single source of league metadata for the frontend.
 *
 * The catalog lives in backend/core/leagues.py and is exposed via
 * GET /api/leagues. The frontend NEVER hardcodes league codes/names.
 * Add a league? → just edit LEAGUES in core/leagues.py.
 */
export function useLeagues() {
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const data = await api.listLeagues();
        if (!ignore) {
          setLeagues(data.leagues);
        }
      } catch (err) {
        if (!ignore) {
          setError(err);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    })();
    return () => { ignore = true; };
  }, []);

  return { leagues, loading, error };
}
