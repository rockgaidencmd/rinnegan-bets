// Port of backend/core/models/europe.py. Constants/weights identical so
// the JS predict output matches Python down to the last decimal.

import {
  normalizeDiff,
  contextSignal,
  blend,
  blendProbabilities,
} from './_shared';

export const EUROPE_VERSION = 'europe_v1';

export const EUROPE_WEIGHTS = {
  xg_diff:         0.30,
  form_diff:       0.20,
  goal_diff:       0.15,
  possession_diff: 0.10,
  home_advantage:  0.15,
  context:         0.10,
};

function computeComponents(home, away, context) {
  return {
    xg_diff: normalizeDiff(
      (home.avg_xg_for || 0) - (home.avg_xg_against || 0),
      (away.avg_xg_for || 0) - (away.avg_xg_against || 0),
      2.0,
    ),
    form_diff: normalizeDiff(home.form_score, away.form_score, 100.0),
    goal_diff: normalizeDiff(
      home.avg_goals_for - home.avg_goals_against,
      away.avg_goals_for - away.avg_goals_against,
      2.0,
    ),
    possession_diff: normalizeDiff(
      home.avg_possession ?? 50.0,
      away.avg_possession ?? 50.0,
      20.0,
    ),
    home_advantage: 0.5,   // constant — home teams ~46% baseline
    context: contextSignal(context),
  };
}

// Returns { pre_score, my_prob, components } — the math half of predict.
// The orchestrator in core/predict.js wraps this with EV/Kelly/verdict.
export function europePreScore(home, away, context, impliedProb) {
  const components = computeComponents(home, away, context);
  const preScore = blend(components, EUROPE_WEIGHTS);
  const myProb = blendProbabilities(preScore, impliedProb);
  return { pre_score: preScore, my_prob: myProb, components };
}
