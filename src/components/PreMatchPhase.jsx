import { TeamForm } from './TeamForm.jsx';
import { TeamStats } from './TeamStats.jsx';

export function PreMatchPhase({ match, onMatchChange, onPhaseChange }) {
  return (
    <>
      <div className="card">
        <div className="card-hdr">
          <div className="card-title">Nombre del partido</div>
        </div>
        <input
          className="match-name-inp"
          placeholder="ej: Barcelona vs Liga de Quito"
          value={match.name}
          onChange={e => onMatchChange({ ...match, name: e.target.value })}
        />
      </div>

      {/* HOME TEAM */}
      <div className="card">
        <div className="team-hdr">
          <div className="team-circle home">L</div>
          <div>
            <input
              className="inp"
              style={{ background: "transparent", border: "none", padding: "0", fontWeight: 800, fontSize: "1rem" }}
              placeholder="Equipo local..."
              value={match.home.name}
              onChange={e => onMatchChange({ ...match, home: { ...match.home, name: e.target.value } })}
            />
            <div className="team-role">LOCAL · Últimos 5 partidos</div>
          </div>
        </div>
        <TeamForm team={match.home} onChange={home => onMatchChange({ ...match, home })} />
        <TeamStats games={match.home.games} />
      </div>

      {/* AWAY TEAM */}
      <div className="card">
        <div className="team-hdr">
          <div className="team-circle away">V</div>
          <div>
            <input
              className="inp"
              style={{ background: "transparent", border: "none", padding: "0", fontWeight: 800, fontSize: "1rem" }}
              placeholder="Equipo visitante..."
              value={match.away.name}
              onChange={e => onMatchChange({ ...match, away: { ...match.away, name: e.target.value } })}
            />
            <div className="team-role">VISITANTE · Últimos 5 partidos</div>
          </div>
        </div>
        <TeamForm team={match.away} onChange={away => onMatchChange({ ...match, away })} />
        <TeamStats games={match.away.games} />
      </div>

      <button className="btn btn-green" onClick={() => onPhaseChange(1)}>
        Continuar → Contexto del partido
      </button>
    </>
  );
}
