// Port of backend/core/bankroll/kelly.py — same formulas + thresholds
// + cap so JS predictions yield identical EV / Kelly / verdict.

export const EV_APOSTAR_MIN = 0.05;      // EV must exceed this to recommend
export const KELLY_APOSTAR_MIN = 0.02;   // AND at least 2% bankroll
export const KELLY_CAP = 0.25;           // never bet > 25%

// EV = p * (odds - 1) * stake  -  (1 - p) * stake.
// Positive → long-run profitable. Stake is the amount at risk.
export function computeEv(prob, odds, stake) {
  const gainIfWin = (odds - 1.0) * stake;
  const lossIfLose = stake;
  return prob * gainIfWin - (1.0 - prob) * lossIfLose;
}

// Kelly fraction f* = (b*p - q) / b  where b = odds-1, q = 1-p.
// Returns 0 when there's no edge or odds <= 1. Capped at KELLY_CAP.
export function kellyFraction(prob, odds, cap = KELLY_CAP) {
  const b = odds - 1.0;
  if (b <= 0 || prob <= 0) return 0.0;
  const q = 1.0 - prob;
  const fStar = (b * prob - q) / b;
  if (fStar <= 0) return 0.0;
  return Math.min(fStar, cap);
}

// Decision tree mirrors Python:
//   ev > 0.05 AND kelly > 0.02  → 'apostar'
//   ev > 0  OR  kelly > 0       → 'esperar'
//   else                        → 'no_apostar'
export function verdictFromEvKelly(ev, kelly, reasonContext = '') {
  const fmt = (n) => n.toFixed(2);
  const pct = (n) => `${(n * 100).toFixed(2)}%`;
  const ctx = reasonContext ? ` ${reasonContext}` : '';

  if (ev > EV_APOSTAR_MIN && kelly > KELLY_APOSTAR_MIN) {
    return { verdict: 'apostar', reason: `EV=${fmt(ev)}, Kelly=${pct(kelly)}.${ctx}` };
  }
  if (ev > 0 || kelly > 0) {
    return { verdict: 'esperar', reason: `Marginal: EV=${fmt(ev)}, Kelly=${pct(kelly)}.${ctx}` };
  }
  return { verdict: 'no_apostar', reason: `No edge: EV=${fmt(ev)}.${ctx}` };
}
