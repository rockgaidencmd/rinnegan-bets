import { useEffect, useState } from 'react';
import { api } from '../utils/api.js';


export function MatchesView() {
  const [matches, setMatches] = useState([]);
  const [leagues, setLeagues] = useState([]);
  const [filterLeague, setFilterLeague] = useState('');
  const [loading, setLoading] = useState(true);

  // Load league list once
  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const data = await api.listLeagues();
        if (!ignore) {
          setLeagues(data.leagues);
        }
      } catch {
        // ignore — leagues filter is optional
      }
    })();
    return () => {
      ignore = true;
    };
  }, []);

  // Re-fetch matches whenever the filter changes
  useEffect(() => {
    let ignore = false;
    setLoading(true);
    (async () => {
      try {
        const data = await api.listMatches({
          league: filterLeague || undefined,
          limit: 50,
        });
        if (!ignore) {
          setMatches(data.matches);
        }
      } catch {
        if (!ignore) {
          setMatches([]);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    })();
    return () => {
      ignore = true;
    };
  }, [filterLeague]);

  return (
    <>
      <div className="view-header">
        <h2 className="view-title">Partidos recientes</h2>
        <span className="view-subtitle">{matches.length} resultados</span>
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

      <div className="matches-list">
        {matches.map((m) => (
          <div key={m.id} className="match-card">
            <div className="match-date mono">
              {new Date(m.match_date).toLocaleDateString('es-EC', { day: '2-digit', month: 'short' })}
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
    </>
  );
}
