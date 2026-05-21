import Constants from 'expo-constants';

const BASE_URL =
  Constants.expoConfig?.extra?.apiUrl ||
  Constants.manifest?.extra?.apiUrl ||
  'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
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
  baseUrl: BASE_URL,
  listLeagues: () => request('/api/leagues'),
  listMatches: ({ league, limit = 25, offset = 0 } = {}) => {
    const params = new URLSearchParams();
    if (league) params.set('league', league);
    params.set('limit', limit);
    params.set('offset', offset);
    return request(`/api/matches?${params.toString()}`);
  },
  getBalance: () => request('/api/bankroll'),
  getBankrollHistory: (limit = 20) =>
    request(`/api/bankroll/history?limit=${limit}`),
};
