import { useTeamData } from '../hooks/useTeamData.js';


/**
 * TeamStatsPreview — compact stat strip shown under the autocomplete-selected team.
 * Uses the shared useTeamData hook so the same fetch logic lives in one place.
 */
export function TeamStatsPreview({ teamId, last = 10 }) {
  const { stats, loading } = useTeamData(teamId, { matchesLimit: last });

  if (loading) {
    return (
      <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: 8 }}>
        Cargando últimos {last} partidos...
      </div>
    );
  }

  if (!stats || stats.matches_analyzed === 0) {
    return (
      <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: 8 }}>
        Sin partidos recientes en BD.
      </div>
    );
  }

  return (
    <div className="stat-row" style={{ marginTop: 12 }}>
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
      {stats.avg_xg_for !== null && (
        <div className="stat-mini">
          <div className="stat-mini-val mono">{stats.avg_xg_for.toFixed(2)}</div>
          <div className="stat-mini-lbl">xG/p</div>
        </div>
      )}
      <div className="stat-mini">
        <div className="stat-mini-val mono">{stats.avg_goals_for.toFixed(1)}</div>
        <div className="stat-mini-lbl">GF/p</div>
      </div>
    </div>
  );
}
