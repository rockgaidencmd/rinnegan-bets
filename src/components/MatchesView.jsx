import { useCallback, useEffect, useState } from 'react';
import { api } from '../utils/api.js';
import { useLeagues } from '../hooks/useLeagues.js';
import { formatDateShort } from '../utils/dates.js';


const PAGE_SIZE = 25;


export function MatchesView() {
  const [matches, setMatches] = useState([]);
  const [filterLeague, setFilterLeague] = useState('');
  const [totalAvailable, setTotalAvailable] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const { leagues } = useLeagues();

  // Reset to page 1 whenever the filter changes
  useEffect(() => {
    let ignore = false;
    setLoading(true);
    (async () => {
      try {
        const data = await api.listMatches({
          league: filterLeague || undefined,
          limit: PAGE_SIZE,
          offset: 0,
        });
        if (!ignore) {
          setMatches(data.matches);
          setTotalAvailable(data.total_available);
        }
      } catch {
        if (!ignore) {
          setMatches([]);
          setTotalAvailable(0);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    })();
    return () => { ignore = true; };
  }, [filterLeague]);

  const loadMore = useCallback(async () => {
    setLoadingMore(true);
    try {
      const data = await api.listMatches({
        league: filterLeague || undefined,
        limit: PAGE_SIZE,
        offset: matches.length,
      });
      setMatches((prev) => [...prev, ...data.matches]);
      setTotalAvailable(data.total_available);
    } catch {
      // best-effort — the user can retry with another click
    } finally {
      setLoadingMore(false);
    }
  }, [filterLeague, matches.length]);

  const hasMore = matches.length < totalAvailable;

  return (
    <>
      <div className="view-header">
        <h2 className="view-title">Partidos recientes</h2>
        <span className="view-subtitle">
          {matches.length} de {totalAvailable} resultados
        </span>
      </div>

      <div className="match-filter">
        <button
          className={`match-filter-chip ${!filterLeague ? 'match-filter-active' : ''}`}
          onClick={() => setFilterLeague('')}
          type="button"
        >
          Todas
        </button>
        {leagues.map((l) => (
          <button
            key={l.code}
            className={`match-filter-chip ${filterLeague === l.code ? 'match-filter-active' : ''}`}
            onClick={() => setFilterLeague(l.code)}
            type="button"
          >
            {l.code}
          </button>
        ))}
      </div>

      {loading && <div className="view-loading">Cargando partidos...</div>}

      {!loading && matches.length === 0 && (
        <div className="view-empty">No hay partidos para este filtro.</div>
      )}

      <div className="matches-list">
        {matches.map((m) => (
          <div key={m.id} className="match-card">
            <div className="match-date mono">
              {formatDateShort(m.match_date)}
              <span className="match-league-chip">{m.league}</span>
            </div>
            <div className="match-teams">
              <span className="match-team match-team-home">{m.home_team_name}</span>
              <span className="match-score-big mono">{m.home_goals}-{m.away_goals}</span>
              <span className="match-team match-team-away">{m.away_team_name}</span>
            </div>
            {m.home_xg !== null && (
              <div className="match-xg-row mono">
                xG: {m.home_xg?.toFixed(2)} - {m.away_xg?.toFixed(2)}
              </div>
            )}
          </div>
        ))}
      </div>

      {!loading && hasMore && (
        <button
          className="btn btn-outline load-more-btn"
          onClick={loadMore}
          disabled={loadingMore}
          type="button"
        >
          {loadingMore ? 'Cargando...' : `Cargar más (${totalAvailable - matches.length} restantes)`}
        </button>
      )}
    </>
  );
}
