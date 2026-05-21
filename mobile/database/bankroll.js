// Port of backend/core/bankroll/tracker.py — same append-only design.
// Balance = last snapshot's balance; available = balance - pending bets.
// Deposits / withdrawals / settle outcomes all INSERT new snapshots.

function lastBalance(db) {
  const row = db.getFirstSync(
    `SELECT balance FROM bankroll_snapshots
     ORDER BY created_at DESC, id DESC LIMIT 1`,
  );
  return row ? row.balance : 0.0;
}

function pendingCommitment(db) {
  const row = db.getFirstSync(
    `SELECT COALESCE(SUM(stake_amount), 0.0) AS s FROM bets
     WHERE outcome = 'pending'`,
  );
  return row.s || 0.0;
}

export function getBalance(db) {
  const current = lastBalance(db);
  const pending = pendingCommitment(db);
  return {
    current,
    available: current - pending,
    pending_commitment: pending,
  };
}

export function getHistory(db, limit = 20) {
  const items = db.getAllSync(
    `SELECT id, balance, change_amount, reason, related_bet_id, created_at
     FROM bankroll_snapshots
     ORDER BY created_at DESC, id DESC
     LIMIT ?`,
    [limit],
  );
  return { items, total: items.length };
}

function insertSnapshot(db, { changeAmount, reason, relatedBetId = null }) {
  const newBalance = lastBalance(db) + changeAmount;
  const createdAt = new Date().toISOString();
  const result = db.runSync(
    `INSERT INTO bankroll_snapshots
     (balance, change_amount, reason, related_bet_id, created_at)
     VALUES (?, ?, ?, ?, ?)`,
    [newBalance, changeAmount, reason, relatedBetId, createdAt],
  );
  return {
    id: result.lastInsertRowId,
    balance: newBalance,
    change_amount: changeAmount,
    reason,
    related_bet_id: relatedBetId,
    created_at: createdAt,
  };
}

export function deposit(db, amount) {
  if (!(amount > 0)) {
    throw new Error('El monto a depositar debe ser mayor a 0.');
  }
  return insertSnapshot(db, { changeAmount: amount, reason: 'deposit' });
}

export function withdraw(db, amount) {
  if (!(amount > 0)) {
    throw new Error('El monto a retirar debe ser mayor a 0.');
  }
  const { available } = getBalance(db);
  if (amount > available) {
    throw new Error(
      `No alcanza el disponible ($${available.toFixed(2)}) para retirar $${amount.toFixed(2)}.`,
    );
  }
  return insertSnapshot(db, { changeAmount: -amount, reason: 'withdrawal' });
}

// Internal — called by bets.settleBet after marking the bet outcome.
export function recordSettlement(db, { betId, outcome, stake, quota }) {
  if (outcome === 'won') {
    const profit = (quota - 1.0) * stake;
    return insertSnapshot(db, {
      changeAmount: profit,
      reason: 'bet_won',
      relatedBetId: betId,
    });
  }
  if (outcome === 'lost') {
    return insertSnapshot(db, {
      changeAmount: -stake,
      reason: 'bet_lost',
      relatedBetId: betId,
    });
  }
  // 'void' — full refund, no net balance change → no snapshot.
  return null;
}
