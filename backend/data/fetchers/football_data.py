"""Football-Data.org v4 API client.

Free tier: 10 requests/min, requires X-Auth-Token header.
Docs: https://www.football-data.org/documentation/api
"""

import os
from datetime import timedelta

from data.cache import CacheService
from data.fetchers.base import BaseFetcher, FetchError


BASE_URL = "https://api.football-data.org/v4"


class FootballDataFetcher(BaseFetcher):
    """Client for Football-Data.org v4 API.

    Coverage (free tier): Premier League, La Liga, Bundesliga, Serie A,
    Ligue 1, Champions League, World Cup, Eurocopa, Championship, etc.

    Does NOT cover: Liga Pro Ecuador, Copa Libertadores (use SofaScore).
    """

    name = "fd"

    def __init__(self, cache: CacheService, api_key: str | None = None):
        super().__init__(cache)
        self._api_key = api_key or os.environ.get("FOOTBALL_DATA_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Football-Data API key required. "
                "Set FOOTBALL_DATA_API_KEY env var or pass api_key param."
            )

    @property
    def _auth_headers(self) -> dict:
        return {"X-Auth-Token": self._api_key}

    def get_competition_teams(self, competition_code: str) -> dict:
        """Get all teams in a competition.

        Example: get_competition_teams("PL") → Premier League teams

        Returns the full response dict with 'teams' array. Caches 24h
        because team rosters change rarely.
        """
        url = f"{BASE_URL}/competitions/{competition_code}/teams"
        return self._fetch_json(
            url,
            cache_key=self._cache_key("teams", competition_code),
            ttl=timedelta(hours=24),
            headers=self._auth_headers,
        )

    def get_competition_matches(
        self, competition_code: str, status: str | None = None
    ) -> dict:
        """Get matches for a competition.

        status: FINISHED | SCHEDULED | LIVE | TIMED (or None for all)
        Cache: 6h (results don't change, but fixtures might).
        """
        url = f"{BASE_URL}/competitions/{competition_code}/matches"
        if status:
            url += f"?status={status}"
        key_status = status or "all"
        return self._fetch_json(
            url,
            cache_key=self._cache_key("matches", competition_code, key_status),
            ttl=timedelta(hours=6),
            headers=self._auth_headers,
        )

    def get_team_matches(self, team_id: int, status: str = "FINISHED") -> dict:
        """Get recent matches for a specific team."""
        url = f"{BASE_URL}/teams/{team_id}/matches?status={status}&limit=10"
        return self._fetch_json(
            url,
            cache_key=self._cache_key("team_matches", team_id, status),
            ttl=timedelta(hours=6),
            headers=self._auth_headers,
        )
