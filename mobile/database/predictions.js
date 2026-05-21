// Predictions table: each user prediction gets persisted so a Bet
// can reference it via prediction_id (FK). Mirror of backend behavior
// except the backend has a separate POST /api/predictions endpoint —
// here predict() in core/predict.js calls savePrediction directly when
// the user taps APOSTAR.

export function savePrediction(db, p) {
  const now = new Date().toISOString();
  const reasoningJson = p.reasoning ? JSON.stringify(p.reasoning) : null;

  // The backend predictions table stores my_prob/implied_prob as 0-100;
  // our predict() returns them as 0-1 to match the API response shape,
  // so we scale up for the DB write.
  const result = db.runSync(
    `INSERT INTO predictions
     (home_team_id, away_team_id, match_date, league, model_version,
      pre_score, implied_prob, my_prob, ev, kelly_fraction,
      quota, stake, verdict, reasoning,
      created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      p.home_team_id, p.away_team_id, p.match_date || now, p.league,
      p.model_version,
      p.pre_score,
      p.implied_prob * 100,
      p.my_prob * 100,
      p.ev, p.kelly,
      p.quota, p.stake, p.verdict,
      reasoningJson,
      now, now,
    ],
  );
  return result.lastInsertRowId;
}

export function getPrediction(db, id) {
  const row = db.getFirstSync('SELECT * FROM predictions WHERE id = ?', [id]);
  if (row && row.reasoning) {
    try { row.reasoning = JSON.parse(row.reasoning); } catch { /* keep raw */ }
  }
  return row;
}
