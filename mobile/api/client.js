import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

const STORAGE_KEY = 'rinnegan.apiUrl';

const DEFAULT_URL =
  Constants.expoConfig?.extra?.apiUrl ||
  Constants.manifest?.extra?.apiUrl ||
  'http://localhost:8000';

// Module-level cache so we don't hit AsyncStorage on every request.
let cachedUrl = null;
const subscribers = new Set();

export async function getApiBaseUrl() {
  if (cachedUrl !== null) return cachedUrl;
  const stored = await AsyncStorage.getItem(STORAGE_KEY);
  cachedUrl = stored || DEFAULT_URL;
  return cachedUrl;
}

export async function setApiBaseUrl(url) {
  const clean = (url || '').trim().replace(/\/+$/, '');
  if (!clean) {
    await AsyncStorage.removeItem(STORAGE_KEY);
    cachedUrl = DEFAULT_URL;
  } else {
    await AsyncStorage.setItem(STORAGE_KEY, clean);
    cachedUrl = clean;
  }
  subscribers.forEach((fn) => fn(cachedUrl));
  return cachedUrl;
}

export function subscribeApiBaseUrl(fn) {
  subscribers.add(fn);
  return () => subscribers.delete(fn);
}

export function getDefaultApiUrl() {
  return DEFAULT_URL;
}

async function request(path, options = {}) {
  const base = await getApiBaseUrl();
  const res = await fetch(`${base}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    // El backend devuelve { title, detail, status } via register_exception_handlers.
    // Preferimos `detail` legible; caemos al statusText si la respuesta no es JSON.
    let message = res.statusText || `HTTP ${res.status}`;
    try {
      const json = await res.json();
      message = json.detail || json.message || json.title || message;
    } catch {
      // not JSON — mantenemos statusText
    }
    throw new Error(message);
  }
  return res.json();
}

export const api = {
  listLeagues: () => request('/api/leagues'),

  listMatches: ({ league, team_id, limit = 25, offset = 0 } = {}) => {
    const params = new URLSearchParams();
    if (league) params.set('league', league);
    if (team_id) params.set('team_id', team_id);
    params.set('limit', limit);
    params.set('offset', offset);
    return request(`/api/matches?${params.toString()}`);
  },

  searchTeams: (q, limit = 10) =>
    request(`/api/teams/search?q=${encodeURIComponent(q)}&limit=${limit}`),

  getTeamsByLeague: (code) =>
    request(`/api/leagues/${encodeURIComponent(code)}/teams`),

  getTeamStats: (teamId) => request(`/api/teams/${teamId}/stats`),

  listFixtures: ({ league, days = 7, limit = 20 } = {}) => {
    const params = new URLSearchParams();
    if (league) params.set('league', league);
    params.set('days', days);
    params.set('limit', limit);
    return request(`/api/fixtures?${params.toString()}`);
  },

  predict: (payload) =>
    request('/api/predictions', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getBalance: () => request('/api/bankroll'),

  getBankrollHistory: (limit = 20) =>
    request(`/api/bankroll/history?limit=${limit}`),

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
};
