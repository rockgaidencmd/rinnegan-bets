"""Tests for fetchers — uses responses library to mock HTTP."""

import pytest
import responses
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from data.cache import CacheService
from data.fetchers.base import BaseFetcher, FetchError
from data.fetchers.football_data import FootballDataFetcher
from data.fetchers.sofascore import SofaScoreFetcher, TOURNAMENT_IDS
from db.base import Base


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def cache(session):
    return CacheService(session)


# --- BaseFetcher tests ---

class _TestableFetcher(BaseFetcher):
    name = "test"


class TestBaseFetcher:

    @responses.activate
    def test_fetch_json_caches_response(self, cache):
        responses.add(
            responses.GET, "https://example.com/data",
            json={"value": 42}, status=200,
        )

        f = _TestableFetcher(cache)
        result = f._fetch_json("https://example.com/data", cache_key="test:k1")

        assert result == {"value": 42}
        # Verify it's in cache
        assert cache.get("test:k1") == {"value": 42}

    @responses.activate
    def test_fetch_json_uses_cache_on_second_call(self, cache):
        responses.add(
            responses.GET, "https://example.com/data",
            json={"value": 1}, status=200,
        )

        f = _TestableFetcher(cache)
        f._fetch_json("https://example.com/data", cache_key="test:k2")

        # Pre-set cache with different value
        cache.set("test:k2", {"value": "from_cache"})

        # Second call should hit cache, NOT make another HTTP call
        result = f._fetch_json("https://example.com/data", cache_key="test:k2")
        assert result == {"value": "from_cache"}
        # Only 1 HTTP call was made
        assert len(responses.calls) == 1

    @responses.activate
    def test_fetch_json_raises_on_404(self, cache):
        responses.add(
            responses.GET, "https://example.com/missing",
            status=404, body="Not Found",
        )

        f = _TestableFetcher(cache)
        with pytest.raises(FetchError, match="HTTP 404"):
            f._fetch_json("https://example.com/missing", cache_key="test:404")

    @responses.activate
    def test_fetch_json_raises_on_invalid_json(self, cache):
        responses.add(
            responses.GET, "https://example.com/bad",
            body="<html>not json</html>", status=200,
        )

        f = _TestableFetcher(cache)
        with pytest.raises(FetchError, match="Invalid JSON"):
            f._fetch_json("https://example.com/bad", cache_key="test:bad")

    @responses.activate
    def test_fetch_json_raises_on_timeout(self, cache):
        from requests.exceptions import Timeout
        responses.add(
            responses.GET, "https://example.com/slow",
            body=Timeout(),
        )

        f = _TestableFetcher(cache)
        with pytest.raises(FetchError, match="Timeout"):
            f._fetch_json("https://example.com/slow", cache_key="test:slow")

    def test_cache_key_namespaced_by_fetcher_name(self, cache):
        f = _TestableFetcher(cache)
        assert f._cache_key("teams", "PL") == "test:teams:PL"


# --- FootballDataFetcher tests ---

class TestFootballDataFetcher:

    def test_requires_api_key(self, cache, monkeypatch):
        monkeypatch.delenv("FOOTBALL_DATA_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key required"):
            FootballDataFetcher(cache)

    def test_accepts_api_key_param(self, cache):
        f = FootballDataFetcher(cache, api_key="explicit-key")
        assert f._api_key == "explicit-key"

    def test_reads_api_key_from_env(self, cache, monkeypatch):
        monkeypatch.setenv("FOOTBALL_DATA_API_KEY", "env-key")
        f = FootballDataFetcher(cache)
        assert f._api_key == "env-key"

    @responses.activate
    def test_get_competition_teams(self, cache):
        responses.add(
            responses.GET, "https://api.football-data.org/v4/competitions/PL/teams",
            json={"teams": [{"id": 1, "name": "Arsenal"}]},
            status=200,
        )

        f = FootballDataFetcher(cache, api_key="test")
        result = f.get_competition_teams("PL")

        assert result["teams"][0]["name"] == "Arsenal"
        # Check auth header was sent
        assert responses.calls[0].request.headers["X-Auth-Token"] == "test"

    @responses.activate
    def test_get_competition_matches_with_status_filter(self, cache):
        responses.add(
            responses.GET,
            "https://api.football-data.org/v4/competitions/PL/matches",
            json={"matches": [{"id": 99}]},
            status=200,
        )

        f = FootballDataFetcher(cache, api_key="test")
        result = f.get_competition_matches("PL", status="FINISHED")

        assert result["matches"][0]["id"] == 99
        # URL should have query param
        assert "status=FINISHED" in responses.calls[0].request.url


# --- SofaScoreFetcher tests ---

class TestSofaScoreFetcher:

    def test_does_not_require_api_key(self, cache):
        # Unlike Football-Data, SofaScore is keyless
        f = SofaScoreFetcher(cache)
        assert f is not None

    def test_tournament_ids_catalog_has_required_leagues(self):
        # These are the ones tu hermano cares about
        required = {"PL", "PD", "CL", "LIB", "EC1"}
        assert required.issubset(TOURNAMENT_IDS.keys())

    @responses.activate
    def test_get_tournament_seasons(self, cache):
        responses.add(
            responses.GET,
            "https://api.sofascore.com/api/v1/unique-tournament/17/seasons",
            json={"seasons": [{"id": 999, "name": "2024/25"}]},
            status=200,
        )

        f = SofaScoreFetcher(cache)
        result = f.get_tournament_seasons(17)
        assert result["seasons"][0]["name"] == "2024/25"

    @responses.activate
    def test_get_event_statistics(self, cache):
        responses.add(
            responses.GET,
            "https://api.sofascore.com/api/v1/event/12345/statistics",
            json={
                "statistics": [{
                    "period": "ALL",
                    "groups": [{
                        "groupName": "Match overview",
                        "statisticsItems": [
                            {"name": "Expected goals", "home": "1.5", "away": "0.8"}
                        ]
                    }]
                }]
            },
            status=200,
        )

        f = SofaScoreFetcher(cache)
        result = f.get_event_statistics(12345)
        xg_stat = result["statistics"][0]["groups"][0]["statisticsItems"][0]
        assert xg_stat["name"] == "Expected goals"
        assert xg_stat["home"] == "1.5"

    @responses.activate
    def test_cache_namespacing_prevents_collisions(self, cache):
        """Both fetchers can cache 'seasons:8' without colliding."""
        responses.add(
            responses.GET,
            "https://api.sofascore.com/api/v1/unique-tournament/8/seasons",
            json={"from": "sofa"}, status=200,
        )

        f = SofaScoreFetcher(cache)
        f.get_tournament_seasons(8)

        # Verify the key is prefixed with fetcher name
        assert cache.get("sofa:seasons:8") == {"from": "sofa"}
        # And NOT under a non-namespaced key
        assert cache.get("seasons:8") is None
