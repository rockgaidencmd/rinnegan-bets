// Shared helpers used by both Europe and Ecuador models.
// Constants and formulas mirror backend/core/models/europe.py exactly.

export const MODEL_BLEND_WEIGHT = 0.4;   // weight on our model
export const MARKET_BLEND_WEIGHT = 0.6;  // weight on market (1 - 0.4)
export const MIN_PROB = 0.05;            // clamp probabilities to this
export const MAX_PROB = 0.95;

export const IMPORTANCE_MULTIPLIER = {
  final:      1.0,
  clasif:     0.5,
  normal:     0.0,
  calendario: -0.5,
};

// Clamp (home - away) / scale to [-1, +1]. The "scale" is the saturation
// point: e.g. a 2.0 xG diff (home much better at xG) maxes the signal.
export function normalizeDiff(homeVal, awayVal, scale) {
  const diff = homeVal - awayVal;
  return Math.max(-1.0, Math.min(1.0, diff / scale));
}

// importance * 0.5 + absence_signal, clamped to [-1, +1].
// Home key absences pull -0.5, away key absences pull +0.5.
export function contextSignal(context) {
  const importance = IMPORTANCE_MULTIPLIER[context.importance] ?? 0.0;
  let absence = 0.0;
  if (context.home_key_absences) absence -= 0.5;
  if (context.away_key_absences) absence += 0.5;
  return Math.max(-1.0, Math.min(1.0, importance * 0.5 + absence));
}

// Weighted average of component signals → 0-100 pre_score.
// 50 = neutral, 100 = all signals max-positive for home, 0 = max-negative.
export function blend(components, weights) {
  let weightedSum = 0.0;
  for (const k of Object.keys(weights)) {
    weightedSum += components[k] * weights[k];
  }
  return Math.max(0.0, Math.min(100.0, 50.0 + weightedSum * 50.0));
}

// Blend our model's probability with the market's implied probability.
// 0.4 * model + 0.6 * market, then clamp to [0.05, 0.95].
export function blendProbabilities(preScore, implied) {
  const modelProb = preScore / 100.0;
  const blended = MODEL_BLEND_WEIGHT * modelProb + MARKET_BLEND_WEIGHT * implied;
  return Math.min(MAX_PROB, Math.max(MIN_PROB, blended));
}
