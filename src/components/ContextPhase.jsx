import { IMP_OPTIONS } from '../utils/calculations.js';

export function ContextPhase({
  match,
  onMatchChange,
  preScore,
  quota,
  stake,
  impliedProb,
  myProb,
  ev,
  onPhaseChange,
}) {
  return (
    <>
      <div className="card">
        <div className="card-hdr">
          <div className="card-title">Importancia del partido</div>
        </div>
        <div className="imp-grid">
          {IMP_OPTIONS.map(o => (
            <div
              key={o.key}
              className={`imp-card ${match.context.importance === o.key ? "sel" : ""}`}
              onClick={() => onMatchChange({ ...match, context: { ...match.context, importance: o.key } })}
            >
              <div className="imp-icon">{o.icon}</div>
              <div className="imp-label">{o.label}</div>
              <div className="imp-sub">{o.sub}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-hdr">
          <div className="card-title">¿Ausencias clave en el local?</div>
        </div>
        <div className="pill-group">
          {[
            { k: "no", l: "No hay ausencias" },
            { k: "si", l: "Sí — titular importante" },
          ].map(o => (
            <div
              key={o.k}
              className={`pill-opt ${match.context.ausencias === o.k ? (o.k === "si" ? "sel-r" : "sel") : ""}`}
              onClick={() => onMatchChange({ ...match, context: { ...match.context, ausencias: o.k } })}
            >
              {o.l}
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-hdr">
          <div className="card-title">Cuota y stake</div>
        </div>
        <div className="g2">
          <div className="field">
            <label className="lbl">Cuota ofrecida</label>
            <input
              className="inp"
              type="number"
              step="0.01"
              placeholder="ej: 1.85"
              value={match.context.quota}
              onChange={e => onMatchChange({ ...match, context: { ...match.context, quota: e.target.value } })}
            />
          </div>
          <div className="field">
            <label className="lbl">Stake ($)</label>
            <input
              className="inp"
              type="number"
              placeholder="ej: 10"
              value={match.context.stake}
              onChange={e => onMatchChange({ ...match, context: { ...match.context, stake: e.target.value } })}
            />
          </div>
        </div>
        {quota > 0 && preScore !== null && (
          <div style={{ background: "var(--s2)", borderRadius: 8, padding: "12px 14px", border: "1px solid var(--border)", marginTop: 6 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--muted)", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                Valor Esperado (EV)
              </span>
              <span className="mono" style={{ fontSize: "1.2rem", fontWeight: 600, color: ev >= 0 ? "var(--green)" : "var(--red)" }}>
                {ev >= 0 ? "+" : ""}{ev?.toFixed(2)}
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
              <span style={{ fontSize: "0.72rem", color: "var(--muted)" }}>
                Prob. implícita: <span className="mono" style={{ color: "var(--text)" }}>{impliedProb.toFixed(1)}%</span>
              </span>
              <span style={{ fontSize: "0.72rem", color: "var(--muted)" }}>
                Mi prob: <span className="mono" style={{ color: "var(--green)" }}>{myProb.toFixed(1)}%</span>
              </span>
              <span style={{ fontSize: "0.72rem", color: "var(--muted)" }}>
                Edge: <span className="mono" style={{ color: myProb > impliedProb ? "var(--green)" : "var(--red)" }}>
                  {(myProb - impliedProb) > 0 ? "+" : ""}{(myProb - impliedProb).toFixed(1)}%
                </span>
              </span>
            </div>
          </div>
        )}
      </div>

      {preScore !== null && (
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">Score prepartido</div>
            <span className={`card-badge ${preScore >= 68 ? "badge-green" : preScore >= 45 ? "badge-yellow" : "badge-red"}`}>
              {preScore.toFixed(0)}/100
            </span>
          </div>
          <div className="prog-wrap">
            <div
              className="prog-bar"
              style={{
                width: `${preScore}%`,
                background: preScore >= 68 ? "var(--green)" : preScore >= 45 ? "var(--yellow)" : "var(--red)",
              }}
            />
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: 8 }}>
            Basado en forma reciente · diferencial de goles · importancia · ausencias
          </div>
        </div>
      )}

      <div className="phase-nav">
        <button className="btn btn-outline" style={{ flex: 1 }} onClick={() => onPhaseChange(0)}>
          ← Volver
        </button>
        <button className="btn btn-green" style={{ flex: 2 }} onClick={() => onPhaseChange(2)}>
          Ir a En Vivo →
        </button>
      </div>
    </>
  );
}
