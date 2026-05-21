import { getBalance, recordSettlement } from './bankroll';

// Mirror of backend's tracker.place_bet — creates a 'pending' bet that
// locks `stake` in pending_commitment until settled.
export function placeBet(db, { prediction_id, quota, stake }) {
  if (!(quota > 1.0)) {
    throw new Error('La cuota debe ser mayor a 1.0.');
  }
  if (!(stake > 0)) {
    throw new Error('El monto a apostar debe ser mayor a 0.');
  }

  const { available } = getBalance(db);
  if (stake > available) {
    throw new Error(
      `No alcanza el disponible ($${available.toFixed(2)}) para apostar $${stake.toFixed(2)}.`,
    );
  }

  const exists = db.getFirstSync(
    'SELECT id FROM predictions WHERE id = ?',
    [prediction_id],
  );
  if (!exists) {
    throw new Error(`Predicción ${prediction_id} no encontrada.`);
  }

  const now = new Date().toISOString();
  const result = db.runSync(
    `INSERT INTO bets
     (prediction_id, quota_used, stake_amount, placed_at,
      outcome, payout_amount, settled_at, created_at, updated_at)
     VALUES (?, ?, ?, ?, 'pending', NULL, NULL, ?, ?)`,
    [prediction_id, quota, stake, now, now, now],
  );

  return {
    id: result.lastInsertRowId,
    prediction_id,
    quota_used: quota,
    stake_amount: stake,
    placed_at: now,
    outcome: 'pending',
    payout_amount: null,
    settled_at: null,
  };
}

// Each pending bet joined with its prediction's matchup for display.
export function listPendingBets(db) {
  return db.getAllSync(
    `SELECT b.id, b.prediction_id, b.quota_used, b.stake_amount, b.placed_at,
            p.league, p.home_team_id, p.away_team_id, p.verdict,
            ht.name AS home_team_name, at.name AS away_team_name
     FROM bets b
     JOIN predictions p ON p.id = b.prediction_id
     JOIN teams ht ON ht.id = p.home_team_id
     JOIN teams at ON at.id = p.away_team_id
     WHERE b.outcome = 'pending'
     ORDER BY b.placed_at DESC`,
  );
}

// Settle a pending bet. outcome ∈ {won, lost, void}. Writes a
// bankroll snapshot for won/lost; void is a full refund with no
// balance change.
export function settleBet(db, betId, outcome) {
  if (!['won', 'lost', 'void'].includes(outcome)) {
    throw new Error(`Outcome inválido: ${outcome}`);
  }

  const bet = db.getFirstSync(
    'SELECT id, quota_used, stake_amount, outcome FROM bets WHERE id = ?',
    [betId],
  );
  if (!bet) {
    throw new Error(`Apuesta ${betId} no encontrada.`);
  }
  if (bet.outcome !== 'pending') {
    throw new Error(`Apuesta ${betId} ya está liquidada (${bet.outcome}).`);
  }

  const settledAt = new Date().toISOString();
  let payout;
  if (outcome === 'won')  payout = bet.stake_amount * bet.quota_used;
  else if (outcome === 'lost') payout = 0.0;
  else /* void */ payout = bet.stake_amount;

  db.runSync(
    `UPDATE bets
     SET outcome = ?, payout_amount = ?, settled_at = ?, updated_at = ?
     WHERE id = ?`,
    [outcome, payout, settledAt, settledAt, betId],
  );

  const snapshot = recordSettlement(db, {
    betId,
    outcome,
    stake: bet.stake_amount,
    quota: bet.quota_used,
  });

  return {
    bet: {
      id: betId,
      quota_used: bet.quota_used,
      stake_amount: bet.stake_amount,
      outcome,
      payout_amount: payout,
      settled_at: settledAt,
    },
    snapshot,
  };
}
