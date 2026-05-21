import { useEffect, useState } from 'react';
import { api } from '../utils/api.js';
import { formatDateTime } from '../utils/dates.js';


const REASON_LABEL = {
  deposit: { icon: '💰', label: 'Depósito', cls: 'res-w' },
  withdrawal: { icon: '💸', label: 'Retiro', cls: 'res-d' },
  bet_won: { icon: '🟢', label: 'Apuesta ganada', cls: 'res-w' },
  bet_lost: { icon: '🔴', label: 'Apuesta perdida', cls: 'res-l' },
  bet_void: { icon: '⏸️', label: 'Apuesta anulada', cls: 'res-d' },
  adjustment: { icon: '✏️', label: 'Ajuste', cls: 'res-d' },
};


export function HistoryView() {
  const [history, setHistory] = useState([]);
  const [roi, setRoi] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const [histData, roiData] = await Promise.all([
          api.getHistory(50),
          api.getRoi(),
        ]);
        if (!ignore) {
          setHistory(histData.items);
          setRoi(roiData);
        }
      } catch {
        // ignore
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
    return <div className="view-loading">Cargando historial...</div>;
  }

  return (
    <>
      <div className="view-header">
        <h2 className="view-title">Historial</h2>
        <span className="view-subtitle">{history.length} movimientos</span>
      </div>

      {roi && roi.bets_settled > 0 && (
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">Rendimiento</div>
            <span className={`card-badge ${roi.roi_pct >= 0 ? 'badge-green' : 'badge-red'}`}>
              ROI {roi.roi_pct >= 0 ? '+' : ''}{roi.roi_pct.toFixed(1)}%
            </span>
          </div>
          <div className="stat-row">
            <div className="stat-mini">
              <div className="stat-mini-val mono">{roi.bets_settled}</div>
              <div className="stat-mini-lbl">Apuestas</div>
            </div>
            <div className="stat-mini">
              <div className="stat-mini-val res-w">{roi.bets_won}</div>
              <div className="stat-mini-lbl">Ganadas</div>
            </div>
            <div className="stat-mini">
              <div className="stat-mini-val res-l">{roi.bets_lost}</div>
              <div className="stat-mini-lbl">Perdidas</div>
            </div>
            <div className="stat-mini">
              <div className="stat-mini-val mono" style={{ color: roi.net_profit >= 0 ? 'var(--green)' : 'var(--red)' }}>
                {roi.net_profit >= 0 ? '+' : ''}${roi.net_profit.toFixed(2)}
              </div>
              <div className="stat-mini-lbl">Neto</div>
            </div>
          </div>
        </div>
      )}

      {history.length === 0 ? (
        <div className="view-empty">No hay movimientos aún. Deposita tu bankroll para empezar.</div>
      ) : (
        <div className="history-list">
          {history.map((h) => {
            const meta = REASON_LABEL[h.reason] || { icon: '·', label: h.reason, cls: '' };
            return (
              <div key={h.id} className="history-row">
                <span className="history-icon">{meta.icon}</span>
                <div className="history-info">
                  <div className="history-reason">{meta.label}</div>
                  <div className="history-date mono">
                    {formatDateTime(h.created_at)}
                  </div>
                </div>
                <div className="history-amount">
                  <span className={`history-change mono ${h.change_amount >= 0 ? 'res-w' : 'res-l'}`}>
                    {h.change_amount >= 0 ? '+' : ''}${h.change_amount.toFixed(2)}
                  </span>
                  <span className="history-balance mono">${h.balance.toFixed(2)}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
