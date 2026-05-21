import { useEffect } from 'react';
import { useTeamData } from '../hooks/useTeamData.js';
import { MatchHistory } from './MatchHistory.jsx';


export function TeamDetailModal({ team, onClose }) {
  const { stats, matches, loading } = useTeamData(team.id);

  useEffect(() => {
    const handleKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} type="button" aria-label="Cerrar">×</button>

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
              <MatchHistory teamId={team.id} matches={matches} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
