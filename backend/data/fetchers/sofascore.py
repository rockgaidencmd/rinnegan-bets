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

from core.leagues import LEAGUES
from data.cache import CacheService
from data.fetchers.base import BaseFetcher


BASE_URL = "https://api.sofascore.com/api/v1"


# Derived from the single source of truth in core/leagues.py.
# To add a new league: edit LEAGUES, not this dict.
TOURNAMENT_IDS = {code: info.sofascore_id for code, info in LEAGUES.items()}


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
        """Get paginated finished events for a team.

        WARNING: page=0 returns events from a PRIOR season, not the most recent.
        For current-season recent matches, use get_team_performance() instead.
        Keeping this method for historical/seasonal queries.
        """
        url = f"{BASE_URL}/team/{team_id}/events/last/{page}"
        return self._fetch_json(
            url,
            cache_key=self._cache_key("team_last", team_id, page),
            ttl=timedelta(hours=1),
        )

    def get_team_performance(self, team_id: int) -> dict:
        """Get team's last 10 ACTUAL recent matches (current form).

        Unlike get_team_last_events(0), this returns truly recent finished
        games across all competitions the team plays in.

        Each event has tournament.uniqueTournament.id which lets us map
        to our internal league code (PL, EC1, CL, etc.) per match instead
        of inheriting the team's home league.

        Cache: 1h.
        """
        url = f"{BASE_URL}/team/{team_id}/performance"
        return self._fetch_json(
            url,
            cache_key=self._cache_key("team_perf", team_id),
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
