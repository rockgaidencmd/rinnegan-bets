import { useEffect, useState } from 'react';
import { api } from '../utils/api.js';


/**
 * useTeamSearch — debounced search-as-you-type for team autocomplete.
 *
 * Returns: { results, loading, error }  for whatever query is current.
 * Empty query → empty results, no API call.
 */
export function useTeamSearch(query, delayMs = 300) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length === 0) {
      setResults([]);
      setError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    let ignore = false;

    const timeoutId = setTimeout(async () => {
      try {
        const data = await api.searchTeams(trimmed);
        if (!ignore) {
          setResults(data.results);
          setError(null);
        }
      } catch (err) {
        if (!ignore) {
          // 404 is expected for typos — show empty, not error
          if (err.status === 404) {
            setResults([]);
            setError(null);
          } else {
            setError(err);
            setResults([]);
          }
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }, delayMs);

    return () => {
      ignore = true;
      clearTimeout(timeoutId);
    };
  }, [query, delayMs]);

  return { results, loading, error };
}
