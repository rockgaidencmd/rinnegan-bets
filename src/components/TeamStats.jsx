import { calcTeamStats } from '../utils/calculations.js';

export function TeamStats({ games }) {
  const stats = calcTeamStats(games);
  if (!stats) return null;

  return (
    <div className="stat-row" style={{ marginTop: 12 }}>
      <div className="stat-mini">
        <div className="stat-mini-val res-w">{stats.wins}G</div>
        <div className="stat-mini-lbl">Ganados</div>
      </div>
      <div className="stat-mini">
        <div className="stat-mini-val res-d">{stats.draws}E</div>
        <div className="stat-mini-lbl">Empates</div>
      </div>
      <div className="stat-mini">
        <div className="stat-mini-val res-l">{stats.losses}P</div>
        <div className="stat-mini-lbl">Perdidos</div>
      </div>
      <div className="stat-mini">
        <div className="stat-mini-val">{stats.avgGF}</div>
        <div className="stat-mini-lbl">GF/prom</div>
      </div>
      <div className="stat-mini">
        <div className="stat-mini-val">{stats.avgGC}</div>
        <div className="stat-mini-lbl">GC/prom</div>
      </div>
    </div>
  );
}
