import { useEffect, useState } from 'react';
import { api } from '../utils/api.js';


/**
 * useFixtures — loads upcoming fixtures for a league.
 *
 * Re-fetches when `league` or `days` changes. Empty league = no call.
 */
export function useFixtures(league, days = 7) {
  const [fixtures, setFixtures] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!league) {
      setFixtures([]);
      return;
    }

    let ignore = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const data = await api.listFixtures({ league, days });
        if (!ignore) {
          setFixtures(data.fixtures);
        }
      } catch (err) {
        if (!ignore) {
          setError(err.message);
          setFixtures([]);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    })();

    return () => { ignore = true; };
  }, [league, days]);

  return { fixtures, loading, error };
}
