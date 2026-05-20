"""SofaScore unofficial API client.

No official docs — endpoints discovered via browser DevTools on sofascore.com.
Coverage: Premier League, La Liga, ALL leagues including Liga Pro Ecuador,
Copa Libertadores, and live in-game stats (xG, possession, shots).

WARNING: Unofficial API. Endpoints can change without notice.
We mitigate this with:
- Aggressive caching (24h on team data, 1h on match data)
- Tests with real captured responses (regression detection)
"""

from datetime import timedelta

from data.cache import CacheService
from data.fetchers.base import BaseFetcher


BASE_URL = "https://api.sofascore.com/api/v1"


# Tournament IDs discovered via DevTools. Keep here as catalog of supported leagues.
# To find new ones: visit league page on sofascore.com, check Network tab for tournament IDs.
TOURNAMENT_IDS = {
    "PL": 17,      # Premier League
    "PD": 8,       # La Liga
    "BL1": 35,     # Bundesliga
    "SA": 23,      # Serie A
    "FL1": 34,     # Ligue 1
    "CL": 7,       # Champions League
    "LIB": 384,    # Copa Libertadores
    "EC1": 240,    # Liga Pro Ecuador (verify with live test)
}


class SofaScoreFetcher(BaseFetcher):
    """Client for SofaScore unofficial API."""

    name = "sofa"

    def get_tournament_seasons(self, tournament_id: int) -> dict:
        """Get all seasons of a tournament.

        Returns dict with 'seasons' array. Latest season is index [0].
        Cache: 7 days (seasons rarely change).
        """
        url = f"{BASE_URL}/unique-tournament/{tournament_id}/seasons"
        return self._fetch_json(
            url,
            cache_key=self._cache_key("seasons", tournament_id),
            ttl=timedelta(days=7),
        )

    def get_season_standings(self, tournament_id: int, season_id: int) -> dict:
        """Get league standings (table). Updated every match day.

        Cache: 12h (standings change but slowly).
        """
        url = f"{BASE_URL}/unique-tournament/{tournament_id}/season/{season_id}/standings/total"
        return self._fetch_json(
            url,
            cache_key=self._cache_key("standings", tournament_id, season_id),
            ttl=timedelta(hours=12),
        )

    def get_season_teams(self, tournament_id: int, season_id: int) -> dict:
        """Get all teams in a season — easier source for catalog than standings.

        Returns dict with 'teams' array.
        Cache: 7 days.
        """
        url = f"{BASE_URL}/unique-tournament/{tournament_id}/season/{season_id}/teams"
        return self._fetch_json(
            url,
            cache_key=self._cache_key("season_teams", tournament_id, season_id),
            ttl=timedelta(days=7),
        )

    def get_team_last_events(self, team_id: int, page: int = 0) -> dict:
        """Get last finished matches of a team (paginated).

        page=0 returns most recent. Each page has ~30 events.
        Cache: 1h (new matches finish frequently during weekends).
        """
        url = f"{BASE_URL}/team/{team_id}/events/last/{page}"
        return self._fetch_json(
            url,
            cache_key=self._cache_key("team_last", team_id, page),
            ttl=timedelta(hours=1),
        )

    def get_event_statistics(self, event_id: int) -> dict:
        """Get full statistics for a single match (xG, possession, shots, etc.)

        Cache: 24h for finished matches (immutable). For live matches,
        caller should invalidate or use shorter TTL.
        """
        url = f"{BASE_URL}/event/{event_id}/statistics"
        return self._fetch_json(
            url,
            cache_key=self._cache_key("event_stats", event_id),
            ttl=timedelta(hours=24),
        )

    def get_live_events(self) -> dict:
        """Get all currently live football matches worldwide.

        Cache: 30 seconds (live data changes fast).
        """
        url = f"{BASE_URL}/sport/football/events/live"
        return self._fetch_json(
            url,
            cache_key=self._cache_key("live"),
            ttl=timedelta(seconds=30),
        )
