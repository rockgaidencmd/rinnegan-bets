import { useEffect, useState } from 'react';
import { api } from '../utils/api.js';


export function TeamDetailModal({ team, onClose }) {
  const [stats, setStats] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const [statsData, matchesData] = await Promise.all([
          api.getTeamStats(team.id, 10),
          api.listMatches({ team_id: team.id, limit: 10 }),
        ]);
        if (!ignore) {
          setStats(statsData);
          setMatches(matchesData.matches);
        }
      } catch {
        if (!ignore) {
          setStats(null);
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
  }, [team.id]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} type="button">×</button>

        <div className="modal-header">
          <div className="modal-team-name">{team.name}</div>
          <div className="modal-team-meta">{team.league} · {team.country || '—'}</div>
        </div>

        {loading && <div className="modal-loading">Cargando datos...</div>}

        {!loading && stats && (
          <>
            <div className="modal-section">
              <div className="modal-section-title">Últimos {stats.matches_analyzed} partidos</div>
              <div className="stat-row">
                <div className="stat-mini">
                  <div className="stat-mini-val res-w">{stats.wins}G</div>
                  <div className="stat-mini-lbl">Gana</div>
                </div>
                <div className="stat-mini">
                  <div className="stat-mini-val res-d">{stats.draws}E</div>
                  <div className="stat-mini-lbl">Emp</div>
                </div>
                <div className="stat-mini">
                  <div className="stat-mini-val res-l">{stats.losses}P</div>
                  <div className="stat-mini-lbl">Pier</div>
                </div>
                <div className="stat-mini">
                  <div className="stat-mini-val mono">{stats.form_score.toFixed(0)}</div>
                  <div className="stat-mini-lbl">Forma</div>
                </div>
              </div>
              <div className="stat-row" style={{ marginTop: 8 }}>
                <div className="stat-mini">
                  <div className="stat-mini-val mono">{stats.avg_goals_for.toFixed(2)}</div>
                  <div className="stat-mini-lbl">GF/p</div>
                </div>
                <div className="stat-mini">
                  <div className="stat-mini-val mono">{stats.avg_goals_against.toFixed(2)}</div>
                  <div className="stat-mini-lbl">GC/p</div>
                </div>
                {stats.avg_xg_for !== null && (
                  <>
                    <div className="stat-mini">
                      <div className="stat-mini-val mono">{stats.avg_xg_for.toFixed(2)}</div>
                      <div className="stat-mini-lbl">xG/p</div>
                    </div>
                    <div className="stat-mini">
                      <div className="stat-mini-val mono">{stats.avg_xg_against.toFixed(2)}</div>
                      <div className="stat-mini-lbl">xGc/p</div>
                    </div>
                  </>
                )}
                {stats.avg_possession !== null && (
                  <div className="stat-mini">
                    <div className="stat-mini-val mono">{stats.avg_possession.toFixed(0)}%</div>
                    <div className="stat-mini-lbl">Pos</div>
                  </div>
                )}
              </div>
            </div>

            <div className="modal-section">
              <div className="modal-section-title">Últimos {matches.length} partidos jugados</div>
              <div className="match-history">
                {matches.map((m) => {
                  const isHome = m.home_team_id === team.id;
                  const teamGoals = isHome ? m.home_goals : m.away_goals;
                  const oppGoals = isHome ? m.away_goals : m.home_goals;
                  const oppName = isHome ? m.away_team_name : m.home_team_name;
                  const won = teamGoals > oppGoals;
                  const drew = teamGoals === oppGoals;
                  const resultClass = won ? 'res-w' : drew ? 'res-d' : 'res-l';
                  const resultLetter = won ? 'G' : drew ? 'E' : 'P';
                  const teamXg = isHome ? m.home_xg : m.away_xg;
                  const oppXg = isHome ? m.away_xg : m.home_xg;
                  return (
                    <div key={m.id} className="match-row">
                      <span className={`match-result ${resultClass}`}>{resultLetter}</span>
                      <span className="match-vs">{isHome ? 'vs' : 'en'}</span>
                      <span className="match-opp">{oppName}</span>
                      <span className="match-score mono">
                        {teamGoals}-{oppGoals}
                      </span>
                      {teamXg !== null && (
                        <span className="match-xg mono">
                          xG: {teamXg?.toFixed(1)}-{oppXg?.toFixed(1)}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
