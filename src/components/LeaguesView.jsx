import { useEffect, useState } from 'react';
import { api } from '../utils/api.js';
import { TeamsByLeague } from './TeamsByLeague.jsx';


export function LeaguesView() {
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedLeague, setExpandedLeague] = useState(null);

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
          setError(err.message);
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
  }, []);

  if (loading) {
    return <div className="view-loading">Cargando ligas...</div>;
  }
  if (error) {
    return <div className="view-error">❌ {error}</div>;
  }

  return (
    <>
      <div className="view-header">
        <h2 className="view-title">Ligas en BD</h2>
        <span className="view-subtitle">{leagues.length} ligas · click para expandir</span>
      </div>

      <div className="leagues-grid">
        {leagues.map((league) => (
          <div
            key={league.code}
            className={`league-card ${expandedLeague === league.code ? 'league-expanded' : ''}`}
          >
            <button
              className="league-card-header"
              onClick={() => setExpandedLeague(expandedLeague === league.code ? null : league.code)}
              type="button"
            >
              <div>
                <div className="league-name">{league.name}</div>
                <div className="league-country">{league.country || '—'}</div>
              </div>
              <div className="league-stats">
                <div className="league-stat">
                  <span className="league-stat-val mono">{league.team_count}</span>
                  <span className="league-stat-lbl">equipos</span>
                </div>
                <div className="league-stat">
                  <span className="league-stat-val mono">{league.match_count}</span>
                  <span className="league-stat-lbl">partidos</span>
                </div>
                <span className="league-chevron">{expandedLeague === league.code ? '▾' : '▸'}</span>
              </div>
            </button>
            {expandedLeague === league.code && (
              <div className="league-card-body">
                <TeamsByLeague leagueCode={league.code} />
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
