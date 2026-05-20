/**
 * Step 3 — bookmaker quota + intended stake.
 */
export function QuotaStakeStep({ quota, onQuotaChange, stake, onStakeChange }) {
  return (
    <div className="card">
      <div className="card-hdr">
        <div className="card-title">3. Cuota y Stake</div>
      </div>
      <div className="g2">
        <div className="field">
          <label className="lbl">Cuota ofrecida</label>
          <input
            className="inp"
            type="number"
            step="0.01"
            min="1.01"
            placeholder="ej: 1.85"
            value={quota}
            onChange={(e) => onQuotaChange(e.target.value)}
          />
        </div>
        <div className="field">
          <label className="lbl">Stake ($)</label>
          <input
            className="inp"
            type="number"
            min="0"
            step="1"
            placeholder="ej: 10"
            value={stake}
            onChange={(e) => onStakeChange(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}
