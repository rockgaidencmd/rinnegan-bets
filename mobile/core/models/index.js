// Factory: league code → model fn. Mirror of backend/core/models/factory.py.

import { LEAGUES } from '../leagues';
import { europePreScore, EUROPE_VERSION, EUROPE_WEIGHTS } from './europe';
import { ecuadorPreScore, ECUADOR_VERSION, ECUADOR_WEIGHTS } from './ecuador';

export function getModelForLeague(leagueCode) {
  const info = LEAGUES[leagueCode];
  if (!info) {
    throw new Error(`No model configured for league '${leagueCode}'`);
  }
  if (info.model_family === 'europe') {
    return { fn: europePreScore, version: EUROPE_VERSION, weights: EUROPE_WEIGHTS };
  }
  if (info.model_family === 'ecuador') {
    return { fn: ecuadorPreScore, version: ECUADOR_VERSION, weights: ECUADOR_WEIGHTS };
  }
  throw new Error(`Unknown model family '${info.model_family}'`);
}
