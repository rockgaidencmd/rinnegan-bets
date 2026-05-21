// Orchestrator: resolve teams → fetch their last matches → extract
// features → run model → compute EV/Kelly/verdict → return same shape
// as backend's POST /api/predictions response.
//
// Mirrors backend/api/routes/predictions.py::predict_match.

import { searchTeams } from '../database/teams';
import { getLastMatchesForTeam } from '../database/matches';
import { extractTeamFeatures } from './features';
import { getModelForLeague } from './models';
import { computeEv, kellyFraction, verdictFromEvKelly } from './kelly';

function pickTeam(db, name) {
  const { results } = searchTeams(db, name, 5);
  if (results.length === 0) {
    throw new Error(`Equipo no encontrado: ${name}`);
  }
  return results[0];
}

function resolveMatchup(home, away, force) {
  if (home.league === away.league) {
    return { home, away, league: home.league };
  }
  if (force) {
    return { home, away, league: home.league };
  }
  throw new Error(
    `'${home.name}' (${home.league}) y '${away.name}' (${away.league}) no comparten liga.`,
  );
}

export function predict(db, {
  home_team,
  away_team,
  quota,
  stake,
  importance = 'normal',
  home_key_absences = false,
  away_key_absences = false,
  force = false,
}) {
  if (!(quota > 1.0)) throw new Error('La cuota debe ser mayor a 1.0.');
  if (!(stake > 0)) throw new Error('El monto debe ser mayor a 0.');

  const homeT = pickTeam(db, home_team);
  const awayT = pickTeam(db, away_team);
  const { home, away, league } = resolveMatchup(homeT, awayT, force);

  const homeMatches = getLastMatchesForTeam(db, home.id, 10);
  const awayMatches = getLastMatchesForTeam(db, away.id, 10);
  const homeFeat = extractTeamFeatures(homeMatches, home.id);
  const awayFeat = extractTeamFeatures(awayMatches, away.id);

  const implied = 1.0 / quota;
  const model = getModelForLeague(league);
  const ctx = { importance, home_key_absences, away_key_absences };
  const { pre_score, my_prob, components } = model.fn(homeFeat, awayFeat, ctx, implied);

  const ev = computeEv(my_prob, quota, stake);
  const kelly = kellyFraction(my_prob, quota);
  const reasonCtx = `form ${homeFeat.form_score.toFixed(0)} vs ${awayFeat.form_score.toFixed(0)}`
    + (homeFeat.avg_xg_for != null && awayFeat.avg_xg_for != null
        ? `, xG ${homeFeat.avg_xg_for.toFixed(1)} vs ${awayFeat.avg_xg_for.toFixed(1)}`
        : '');
  const { verdict, reason } = verdictFromEvKelly(ev, kelly, reasonCtx);

  return {
    home_team: home.name,
    away_team: away.name,
    league,
    market: 'victoria_local',
    model_version: model.version,
    home_team_id: home.id,
    away_team_id: away.id,
    my_prob,
    implied_prob: implied,
    edge: my_prob - implied,
    quota,
    stake,
    ev,
    kelly,
    pre_score,
    verdict,
    verdict_reason: reason,
    reasoning: { components, weights: model.weights },
  };
}
