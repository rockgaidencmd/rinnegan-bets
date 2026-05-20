import { VerdictBox } from './VerdictBox.jsx';

export function LivePhase({
  match,
  onMatchChange,
  finalScore,
  verdict,
  liveEV,
  liveImpliedProb,
  liveMyProb,
  liveEdge,
  quota,
  liveQuota,
  onPhaseChange,
}) {
  return (
    <>
      <div className="card">
        <div className="card-hdr">
          <div className="card-title">🔴 Datos en vivo — copia de tu app de resultados</div>
          <div className="card-badge badge-red">EN VIVO</div>
        </div>

        <div className="field">
          <label className="lbl">Minuto del partido</label>
          <input
            className="inp"
            type="number"
            min="0"
            max="120"
            placeholder="45"
            value={match.live.minuto}
            onChange={e => onMatchChange({ ...match, live: { ...match.live, minuto: e.target.value } })}
          />
        </div>

        {/* LIVE QUOTA */}
        <div style={{ background: "var(--s2)", border: "1px solid rgba(245,196,0,0.25)", borderRadius: 9, padding: "14px", marginBottom: 10 }}>
          <div style={{ fontSize: "0.68rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--yellow)", marginBottom: 10 }}>
            ⚡ Cuota actual en vivo
          </div>
          <div className="g2">
            <div className="field" style={{ marginBottom: 0 }}>
              <label className="lbl">Cuota en vivo</label>
              <input
                className="inp"
                type="number"
                step="0.01"
                placeholder="ej: 1.60"
                style={{ borderColor: liveQuota > 0 ? "rgba(245,196,0,0.4)" : "" }}
                value={match.live.liveQuota}
                onChange={e => onMatchChange({ ...match, live: { ...match.live, liveQuota: e.target.value } })}
              />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label className="lbl">Stake en vivo ($)</label>
              <input
                className="inp"
                type="number"
                placeholder="10"
                value={match.live.liveStake}
                onChange={e => onMatchChange({ ...match, live: { ...match.live, liveStake: e.target.value } })}
              />
            </div>
          </div>
          {liveEV !== null && (
            <div style={{ marginTop: 12, padding: "10px 12px", borderRadius: 8, background: liveEV >= 0 ? "rgba(0,245,160,0.07)" : "rgba(255,61,90,0.07)", border: `1px solid ${liveEV >= 0 ? "rgba(0,245,160,0.3)" : "rgba(255,61,90,0.3)"}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                  EV en vivo
                </span>
                <span className="mono" style={{ fontSize: "1.3rem", fontWeight: 700, color: liveEV >= 0 ? "var(--green)" : "var(--red)" }}>
                  {liveEV >= 0 ? "+" : ""}{liveEV.toFixed(2)}
                </span>
              </div>
              <div style={{ display: "flex", gap: 16, marginTop: 7 }}>
                <span style={{ fontSize: "0.7rem", color: "var(--muted)" }}>
                  Prob. implícita: <span className="mono" style={{ color: "var(--text)" }}>{liveImpliedProb.toFixed(1)}%</span>
                </span>
                <span style={{ fontSize: "0.7rem", color: "var(--muted)" }}>
                  Mi prob: <span className="mono" style={{ color: "var(--green)" }}>{liveMyProb.toFixed(1)}%</span>
                </span>
                <span style={{ fontSize: "0.7rem", color: "var(--muted)" }}>
                  Edge: <span className="mono" style={{ color: liveEdge > 0 ? "var(--green)" : "var(--red)" }}>
                    {liveEdge > 0 ? "+" : ""}{liveEdge.toFixed(1)}%
                  </span>
                </span>
              </div>
              {quota > 0 && liveQuota !== quota && (
                <div style={{ marginTop: 7, fontSize: "0.68rem", color: "var(--muted)" }}>
                  Cuota prepartido: <span className="mono" style={{ color: "var(--muted)" }}>{quota}</span>
                  {liveQuota < quota
                    ? <span style={{ color: "var(--red)", marginLeft: 6 }}>↓ bajó {(quota - liveQuota).toFixed(2)} — mercado anticipa gol</span>
                    : <span style={{ color: "var(--green)", marginLeft: 6 }}>↑ subió {(liveQuota - quota).toFixed(2)} — oportunidad abierta</span>
                  }
                </div>
              )}
            </div>
          )}
        </div>

        <hr className="sep" />

        <div style={{ marginBottom: 10 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 8, alignItems: "center", marginBottom: 10 }}>
            <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--blue)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              {match.home.name || "Local"}
            </div>
            <div style={{ fontSize: "0.65rem", color: "var(--muted)", textAlign: "center" }}>VS</div>
            <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--red)", textTransform: "uppercase", letterSpacing: "0.08em", textAlign: "right" }}>
              {match.away.name || "Visitante"}
            </div>
          </div>

          {[
            { label: "Posesión %", lKey: "posLocal", rKey: "posVisit", hint: "Suma debe dar 100" },
            { label: "Ataques peligrosos", lKey: "ataLocal", rKey: "ataVisit", hint: "" },
            { label: "Tiros de esquina", lKey: "corLocal", rKey: "corVisit", hint: "" },
            { label: "Tarjetas amarillas", lKey: "tarLocal", rKey: "tarVisit", hint: "" },
          ].map(row => (
            <div key={row.label} style={{ marginBottom: 10 }}>
              <div style={{ fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)", textAlign: "center", marginBottom: 5 }}>
                {row.label}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 8, alignItems: "center" }}>
                <input
                  className="inp"
                  type="number"
                  min="0"
                  placeholder="0"
                  style={{ textAlign: "center", borderColor: "rgba(68,136,255,0.3)" }}
                  value={match.live[row.lKey]}
                  onChange={e => onMatchChange({ ...match, live: { ...match.live, [row.lKey]: e.target.value } })}
                />
                <div style={{ width: 8, height: 1, background: "var(--border)" }} />
                <input
                  className="inp"
                  type="number"
                  min="0"
                  placeholder="0"
                  style={{ textAlign: "center", borderColor: "rgba(255,61,90,0.3)" }}
                  value={match.live[row.rKey]}
                  onChange={e => onMatchChange({ ...match, live: { ...match.live, [row.rKey]: e.target.value } })}
                />
              </div>
              {row.hint && <div style={{ fontSize: "0.62rem", color: "var(--muted)", textAlign: "center", marginTop: 3 }}>{row.hint}</div>}
            </div>
          ))}
        </div>
      </div>

      {/* VERDICT */}
      <VerdictBox verdict={verdict} finalScore={finalScore} liveEV={liveEV} />

      <button className="btn btn-outline" style={{ marginTop: 12 }} onClick={() => onPhaseChange(1)}>
        ← Volver al contexto
      </button>
    </>
  );
}
