// Standalone client. Same `api.*` shape the screens already consume,
// but every method now reads/writes the local SQLite (mobile/database/*)
// and runs the prediction in-process (mobile/core/predict). No HTTP.
//
// All methods stay async so the screens (which `await` everything)
// don't need any change.

import { getDb } from '../database';
import { listLeagues } from '../database/leagues';
import { searchTeams, getTeamsByLeague, getTeamStats } from '../database/teams';
import { listMatches } from '../database/matches';
import { listFixtures } from '../database/fixtures';
import {
  getBalance,
  getHistory as getBankrollHistory,
  deposit,
  withdraw,
} from '../database/bankroll';
import { placeBet, listPendingBets, settleBet } from '../database/bets';
import { savePrediction } from '../database/predictions';
import { predict as runPredict } from '../core/predict';

// Small helper: run a sync DAO in a Promise so the screens'
// `await api.foo()` continues to work.
function defer(fn) {
  return (...args) =>
    new Promise((resolve, reject) => {
      try {
        resolve(fn(getDb(), ...args));
      } catch (e) {
        reject(e);
      }
    });
}

export const api = {
  listLeagues: defer(listLeagues),

  listMatches: defer((db, params = {}) => listMatches(db, params)),

  searchTeams: defer((db, q, limit) => searchTeams(db, q, limit)),

  getTeamsByLeague: defer((db, code) => getTeamsByLeague(db, code)),

  getTeamStats: defer((db, teamId) => getTeamStats(db, teamId)),

  listFixtures: defer((db, params = {}) => listFixtures(db, params)),

  predict: defer((db, payload) => runPredict(db, payload)),

  getBalance: defer(getBalance),

  getBankrollHistory: defer((db, limit) => getBankrollHistory(db, limit)),

  deposit: defer((db, amount) => deposit(db, amount)),

  withdraw: defer((db, amount) => withdraw(db, amount)),

  // New endpoints exposed for the bet flow (no HTTP equivalents needed).
  savePrediction: defer((db, p) => savePrediction(db, p)),
  placeBet: defer((db, params) => placeBet(db, params)),
  listPendingBets: defer(listPendingBets),
  settleBet: defer((db, betId, outcome) => settleBet(db, betId, outcome)),
};
