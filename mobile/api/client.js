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
    const body = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status}: ${body || res.statusText}`);
  }
  return res.json();
}

export const api = {
  listLeagues: () => request('/api/leagues'),

  listMatches: ({ league, limit = 25, offset = 0 } = {}) => {
    const params = new URLSearchParams();
    if (league) params.set('league', league);
    params.set('limit', limit);
    params.set('offset', offset);
    return request(`/api/matches?${params.toString()}`);
  },

  searchTeams: (q, limit = 10) =>
    request(`/api/teams/search?q=${encodeURIComponent(q)}&limit=${limit}`),

  predict: (payload) =>
    request('/api/predictions', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getBalance: () => request('/api/bankroll'),

  getBankrollHistory: (limit = 20) =>
    request(`/api/bankroll/history?limit=${limit}`),
};
