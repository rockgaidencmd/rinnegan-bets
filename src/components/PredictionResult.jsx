/**
 * PredictionResult — shows verdict + EV + Kelly + stakes.
 *
 * Receives a prediction object from POST /api/predictions and renders
 * a human-readable verdict screen mirroring the CLI output.
 */

const VERDICT_CONFIG = {
  apostar: { cls: 'go', icon: '🟢', label: 'APOSTAR', sub: 'Señales sólidas detectadas' },
  esperar: { cls: 'wait', icon: '🟡', label: 'ESPERAR', sub: 'Edge marginal, espera más info' },
  no_apostar: { cls: 'no', icon: '🔴', label: 'NO APOSTAR', sub: 'Sin edge, no apuestes' },
};


export function PredictionResult({ prediction, availableBalance, onReset }) {
  const v = VERDICT_CONFIG[prediction.verdict];
  const edge = prediction.edge * 100;
  const profitIfWin = prediction.stake * prediction.quota - prediction.stake;
  const recommendedStake = availableBalance > 0 ? prediction.kelly * availableBalance : 0;
  const overKelly = prediction.stake > recommendedStake * 1.2;

  return (
    <>
      <div className="card">
        <div className="card-hdr">
          <div className="card-title">Resultado del Análisis</div>
          <span className={`card-badge ${v.cls === 'go' ? 'badge-green' : v.cls === 'wait' ? 'badge-yellow' : 'badge-red'}`}>
            {prediction.league} · {prediction.model_version}
          </span>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: 14 }}>
          {prediction.home_team} <span style={{ color: 'var(--muted)' }}>vs</span> {prediction.away_team}
          <br />
          <span style={{ fontSize: '0.7rem' }}>Mercado: Victoria Local · Cuota: {prediction.quota.toFixed(2)}</span>
        </div>

        <div className={`verdict ${v.cls}`}>
          <div className="verdict-icon">{v.icon}</div>
          <div className={`verdict-main ${v.cls}`}>{v.label}</div>
          <div className="verdict-sub">{v.sub}</div>
          <div className="verdict-score mono">
            apuestas a que GANA <strong>{prediction.home_team}</strong>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-hdr">
          <div className="card-title">Probabilidades</div>
        </div>
        <div className="stat-row">
          <div className="stat-mini">
            <div className="stat-mini-val mono">{(prediction.my_prob * 100).toFixed(1)}%</div>
            <div className="stat-mini-lbl">Tu Prob</div>
          </div>
          <div className="stat-mini">
            <div className="stat-mini-val mono">{(prediction.implied_prob * 100).toFixed(1)}%</div>
            <div className="stat-mini-lbl">Mercado</div>
          </div>
          <div className="stat-mini">
            <div className="stat-mini-val mono" style={{ color: edge >= 0 ? 'var(--green)' : 'var(--red)' }}>
              {edge >= 0 ? '+' : ''}{edge.toFixed(1)}%
            </div>
            <div className="stat-mini-lbl">Edge</div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-hdr">
          <div className="card-title">Si apuestas ${prediction.stake.toFixed(0)}</div>
        </div>
        <div style={{ marginBottom: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
            <span style={{ color: 'var(--muted)' }}>✅ Gana {prediction.home_team}</span>
            <span className="mono" style={{ color: 'var(--green)' }}>
              cobras ${(prediction.stake * prediction.quota).toFixed(2)} (+${profitIfWin.toFixed(2)})
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
            <span style={{ color: 'var(--muted)' }}>❌ Empata o gana {prediction.away_team}</span>
            <span className="mono" style={{ color: 'var(--red)' }}>
              pierdes ${prediction.stake.toFixed(2)}
            </span>
          </div>
          <hr className="sep" />
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
            <span style={{ color: 'var(--muted)' }}>📊 EV (esperado a la larga)</span>
            <span className="mono" style={{ color: prediction.ev >= 0 ? 'var(--green)' : 'var(--red)', fontSize: '1rem', fontWeight: 700 }}>
              {prediction.ev >= 0 ? '+' : ''}${prediction.ev.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {prediction.kelly > 0 && (
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">Recomendación de Kelly</div>
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700 }} className="mono">
            ${recommendedStake.toFixed(2)} <span style={{ fontSize: '0.7rem', color: 'var(--muted)', fontWeight: 400 }}>({(prediction.kelly * 100).toFixed(1)}% de ${availableBalance.toFixed(2)})</span>
          </div>
          {overKelly && (
            <div style={{ fontSize: '0.75rem', color: 'var(--yellow)', marginTop: 6 }}>
              ⚠️ Estás apostando más que Kelly — riesgo elevado.
            </div>
          )}
        </div>
      )}

      <button className="btn btn-outline" onClick={onReset} type="button">
        ← Nueva predicción
      </button>
    </>
  );
}
