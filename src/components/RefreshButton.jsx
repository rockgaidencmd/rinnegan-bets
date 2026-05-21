import { useEffect, useState } from 'react';
import { api } from '../utils/api.js';


const POLL_INTERVAL_MS = 5000;     // Check stats every 5s while refreshing
const POLL_DURATION_MS = 12 * 60 * 1000;  // Stop polling after 12 min


/**
 * RefreshButton — sidebar action that triggers a backend re-seed.
 *
 * Click → POST /api/admin/refresh (returns 202 immediately, work runs
 * in the background). The button enters "refreshing" state and polls
 * /api/admin/stats every 5s; once match count grows, it celebrates.
 */
export function RefreshButton({ collapsed }) {
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState(null);
  const [initialMatches, setInitialMatches] = useState(null);
  const [error, setError] = useState(null);

  // Load initial stats once on mount
  useEffect(() => {
    let ignore = false;
    api.getDataStats()
      .then((data) => { if (!ignore) setStats(data); })
      .catch(() => {});
    return () => { ignore = true; };
  }, []);

  // Poll while refreshing
  useEffect(() => {
    if (!refreshing) return;

    const startTime = Date.now();
    const interval = setInterval(async () => {
      if (Date.now() - startTime > POLL_DURATION_MS) {
        setRefreshing(false);
        return;
      }
      try {
        const fresh = await api.getDataStats();
        setStats(fresh);
        // Heuristic: if matches count grew or fetched_at advanced, consider done.
        // Simplest: keep polling until duration ceiling.
      } catch {
        // ignore transient errors
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [refreshing]);

  const handleClick = async () => {
    setError(null);
    try {
      const current = await api.getDataStats();
      setInitialMatches(current.matches);
      setStats(current);
      await api.refreshData();
      setRefreshing(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const matchesGained = stats && initialMatches !== null
    ? Math.max(0, stats.matches - initialMatches)
    : 0;

  return (
    <div className={`refresh-control ${collapsed ? 'refresh-control-collapsed' : ''}`}>
      <button
        className="refresh-btn"
        onClick={handleClick}
        disabled={refreshing}
        type="button"
        title={refreshing ? 'Actualizando data... (5-10 min)' : 'Actualizar data desde SofaScore'}
      >
        <span className={`refresh-icon ${refreshing ? 'refresh-icon-spinning' : ''}`}>↻</span>
        {!collapsed && (
          <span className="refresh-label">
            {refreshing ? 'Actualizando...' : 'Actualizar data'}
          </span>
        )}
      </button>
      {!collapsed && stats && (
        <div className="refresh-stats">
          {stats.matches} partidos · {stats.teams} equipos
          {refreshing && matchesGained > 0 && (
            <span className="refresh-gained"> · +{matchesGained}</span>
          )}
        </div>
      )}
      {!collapsed && error && (
        <div className="refresh-error">❌ {error}</div>
      )}
    </div>
  );
}
