// Port of backend/core/models/ecuador.py. Uses shots_on_target as the
// xG proxy since SofaScore doesn't publish xG for LigaPro EC1 / LIB.

import {
  normalizeDiff,
  contextSignal,
  blend,
  blendProbabilities,
} from './_shared';

export const ECUADOR_VERSION = 'ecuador_v1';

export const ECUADOR_WEIGHTS = {
  shots_diff:      0.25,
  form_diff:       0.20,
  goal_diff:       0.15,
  possession_diff: 0.15,
  home_advantage:  0.20,  // stronger than Europe — altitude + crowd
  context:         0.05,  // less weight, sparse context data
};

function computeComponents(home, away, context) {
  return {
    shots_diff: normalizeDiff(
      home.avg_shots_on_target ?? 3.0,
      away.avg_shots_on_target ?? 3.0,
      4.0,
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
    home_advantage: 0.6,
    context: contextSignal(context),
  };
}

export function ecuadorPreScore(home, away, context, impliedProb) {
  const components = computeComponents(home, away, context);
  const preScore = blend(components, ECUADOR_WEIGHTS);
  const myProb = blendProbabilities(preScore, impliedProb);
  return { pre_score: preScore, my_prob: myProb, components };
}
