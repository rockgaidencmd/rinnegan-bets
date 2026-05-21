// Port of backend/core/leagues.py — the single source of truth for
// league metadata. Mirrored exactly so prediction outputs match between
// the backend and the mobile.

export const LEAGUES = {
  PL:  { code: 'PL',  name: 'Premier League',     country: 'England',       sofascore_id: 17,    football_data_id: 'PL',  model_family: 'europe'  },
  PD:  { code: 'PD',  name: 'La Liga',            country: 'Spain',         sofascore_id: 8,     football_data_id: 'PD',  model_family: 'europe'  },
  BL1: { code: 'BL1', name: 'Bundesliga',         country: 'Germany',       sofascore_id: 35,    football_data_id: 'BL1', model_family: 'europe'  },
  SA:  { code: 'SA',  name: 'Serie A',            country: 'Italy',         sofascore_id: 23,    football_data_id: 'SA',  model_family: 'europe'  },
  FL1: { code: 'FL1', name: 'Ligue 1',            country: 'France',        sofascore_id: 34,    football_data_id: 'FL1', model_family: 'europe'  },
  CL:  { code: 'CL',  name: 'Champions League',   country: 'Europe',        sofascore_id: 7,     football_data_id: 'CL',  model_family: 'europe'  },
  LIB: { code: 'LIB', name: 'Copa Libertadores',  country: 'South America', sofascore_id: 16940, football_data_id: null,  model_family: 'ecuador' },
  EC1: { code: 'EC1', name: 'LigaPro Ecuador',    country: 'Ecuador',       sofascore_id: 240,   football_data_id: null,  model_family: 'ecuador' },
};

export function bySofascoreId(sofaId) {
  for (const info of Object.values(LEAGUES)) {
    if (info.sofascore_id === sofaId) return info;
  }
  return null;
}

export function codesForModel(family) {
  return Object.values(LEAGUES)
    .filter((i) => i.model_family === family)
    .map((i) => i.code);
}
