export function VerdictBox({ verdict, finalScore, liveEV }) {
  return (
    <div className={`verdict ${verdict.cls}`}>
      <div className="verdict-icon">{verdict.icon}</div>
      <div className={`verdict-main ${verdict.cls}`}>{verdict.label}</div>
      <div className="verdict-sub">{verdict.sub}</div>
      <div className="verdict-score mono">
        Score final: {finalScore.toFixed(0)}/100
        {liveEV !== null && ` · EV en vivo: ${liveEV >= 0 ? "+" : ""}${liveEV.toFixed(2)}`}
      </div>
      {liveEV !== null && (
        <div style={{
          marginTop: 10,
          fontSize: "0.75rem",
          padding: "6px 14px",
          borderRadius: 99,
          display: "inline-block",
          background: liveEV >= 0 ? "rgba(0,245,160,0.1)" : "rgba(255,61,90,0.1)",
          color: liveEV >= 0 ? "var(--green)" : "var(--red)",
          fontFamily: "'IBM Plex Mono',monospace"
        }}>
          {liveEV >= 0 ? "✅ EV POSITIVO EN VIVO" : "❌ EV NEGATIVO EN VIVO"}
        </div>
      )}
    </div>
  );
}
