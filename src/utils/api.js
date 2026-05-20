/**
 * API client — wraps fetch with error handling and base URL.
 *
 * Base URL is configurable via VITE_API_URL env var (defaults to localhost:8000).
 * To override: create .env.local with `VITE_API_URL=http://192.168.x.x:8000`
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';


export class ApiError extends Error {
  constructor(status, body) {
    super(body?.detail || body?.title || `HTTP ${status}`);
    this.status = status;
    this.body = body;
  }
}


async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  let body = null;
  try {
    body = await response.json();
  } catch {
    // Empty body or non-JSON response
  }

  if (!response.ok) {
    throw new ApiError(response.status, body);
  }

  return body;
}


export const api = {
  // Health
  health: () => request('/health'),

  // Teams
  searchTeams: (q, limit = 10) =>
    request(`/api/teams/search?q=${encodeURIComponent(q)}&limit=${limit}`),

  getTeam: (id) => request(`/api/teams/${id}`),

  getTeamStats: (id, last = 10) =>
    request(`/api/teams/${id}/stats?last=${last}`),

  // Catalog (Phase 8 — explore)
  listLeagues: () => request('/api/leagues'),

  getTeamsByLeague: (code) => request(`/api/leagues/${code}/teams`),

  listMatches: ({ league, team_id, limit = 20 } = {}) => {
    const params = new URLSearchParams();
    if (league) params.set('league', league);
    if (team_id) params.set('team_id', team_id);
    params.set('limit', limit);
    return request(`/api/matches?${params.toString()}`);
  },

  // Predictions
  predict: (body) =>
    request('/api/predictions', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // Bankroll
  getBankroll: () => request('/api/bankroll'),

  deposit: (amount) =>
    request('/api/bankroll/deposit', {
      method: 'POST',
      body: JSON.stringify({ amount }),
    }),

  withdraw: (amount) =>
    request('/api/bankroll/withdraw', {
      method: 'POST',
      body: JSON.stringify({ amount }),
    }),

  placeBet: (prediction_id, quota, stake) =>
    request('/api/bankroll/bets', {
      method: 'POST',
      body: JSON.stringify({ prediction_id, quota, stake }),
    }),

  settleBet: (bet_id, outcome) =>
    request(`/api/bankroll/bets/${bet_id}/settle`, {
      method: 'POST',
      body: JSON.stringify({ outcome }),
    }),

  getRoi: () => request('/api/bankroll/roi'),
  getHistory: (limit = 20) => request(`/api/bankroll/history?limit=${limit}`),
};
