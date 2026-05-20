"""
Real tests for APIValidator — tests the actual code, not hardcoded dicts.

Uses the `responses` library to mock HTTP without hitting real APIs.
"""

import time
import pytest
import responses

from scripts.validate_apis import APIValidator


# --- _get_with_details: tests the HTTP helper ---

class TestGetWithDetails:

    @responses.activate
    def test_returns_status_size_and_elapsed_on_200(self):
        responses.add(
            responses.GET,
            "https://example.com/ok",
            json={"hello": "world"},
            status=200,
        )

        v = APIValidator()
        result = v._get_with_details("https://example.com/ok", timeout=5.0)

        assert result["status_code"] == 200
        assert result["response_size_bytes"] > 0
        assert result["error"] is None
        assert "elapsed_ms" in result

    @responses.activate
    def test_extracts_content_sample_max_300_chars(self):
        long_body = "x" * 1000
        responses.add(
            responses.GET, "https://example.com/long",
            body=long_body, status=200
        )

        v = APIValidator()
        result = v._get_with_details("https://example.com/long")

        assert len(result["sample"]) <= 300

    @responses.activate
    def test_handles_404_without_crashing(self):
        responses.add(
            responses.GET, "https://example.com/missing",
            status=404, body="Not Found"
        )

        v = APIValidator()
        result = v._get_with_details("https://example.com/missing")

        assert result["status_code"] == 404
        assert result["error"] is None  # 404 is a response, not an error

    @responses.activate
    def test_returns_timeout_error_on_timeout(self):
        from requests.exceptions import Timeout

        responses.add(
            responses.GET, "https://example.com/slow",
            body=Timeout()
        )

        v = APIValidator()
        result = v._get_with_details("https://example.com/slow", timeout=0.5)

        assert result["status_code"] is None
        assert "TIMEOUT" in result["error"]

    @responses.activate
    def test_returns_connection_error_when_unreachable(self):
        from requests.exceptions import ConnectionError as ReqConnectionError

        responses.add(
            responses.GET, "https://example.com/dead",
            body=ReqConnectionError("Connection refused")
        )

        v = APIValidator()
        result = v._get_with_details("https://example.com/dead")

        assert result["status_code"] is None
        assert "CONNECTION_ERROR" in result["error"]


# --- test_football_data_org: tests classification logic ---

class TestFootballDataValidation:

    @responses.activate
    def test_marks_ok_when_200_with_api_key(self):
        responses.add(
            responses.GET, "https://api.football-data.org/v4/competitions/PL",
            json={"name": "Premier League"},
            status=200,
        )

        v = APIValidator(football_data_key="fake-key")
        result = v.test_football_data_org()

        assert result["status"] == "✅"
        assert "Premier" in result["result"]

    @responses.activate
    def test_marks_warning_when_403_without_key(self):
        responses.add(
            responses.GET, "https://api.football-data.org/v4/competitions/PL",
            status=403,
        )

        v = APIValidator(football_data_key=None)
        result = v.test_football_data_org()

        assert result["status"] == "⚠️"
        assert "API_KEY" in result["result"] or "key" in result["result"].lower()

    @responses.activate
    def test_marks_warning_on_rate_limit(self):
        responses.add(
            responses.GET, "https://api.football-data.org/v4/competitions/PL",
            status=429,
        )

        v = APIValidator(football_data_key="fake-key")
        result = v.test_football_data_org()

        assert result["status"] == "⚠️"
        assert "Rate" in result["result"]


# --- test_fbref: classification logic ---

class TestFBRefValidation:

    @responses.activate
    def test_marks_ok_when_xg_keyword_present(self):
        html = "<html><body>Premier League stats with xG table</body></html>"
        responses.add(
            responses.GET,
            "https://fbref.com/en/comps/9/Premier-League-Stats",
            body=html, status=200,
        )

        v = APIValidator()
        result = v.test_fbref()

        assert result["status"] == "✅"
        assert "xG" in result["result"]

    @responses.activate
    def test_marks_warning_when_blocked_403(self):
        responses.add(
            responses.GET,
            "https://fbref.com/en/comps/9/Premier-League-Stats",
            status=403,
        )

        v = APIValidator()
        result = v.test_fbref()

        assert result["status"] == "⚠️"
        assert "Blocked" in result["result"] or "User-Agent" in result["result"]


# --- run_all: integration test ---

class TestRunAll:

    @responses.activate
    def test_run_all_completes_quickly_with_all_mocked(self):
        # All endpoints mocked so this should be very fast
        for url in [
            "https://api.football-data.org/v4/competitions/PL",
            "https://fbref.com/en/comps/9/Premier-League-Stats",
            "https://api.sofascore.com/api/v1/unique-tournament/8/seasons",
            "https://api.sofascore.com/api/v1/sport/football/events/live",
        ]:
            responses.add(responses.GET, url, json={"ok": True}, status=200)

        v = APIValidator(football_data_key="fake-key")
        start = time.time()
        results = v.run_all()
        elapsed = time.time() - start

        # 4 tests, all mocked, should complete in <2 seconds
        assert elapsed < 2.0
        assert len(results) == 4
        assert all(r["status"] == "✅" for r in results)

    @responses.activate
    def test_run_all_does_not_hang_when_apis_fail(self):
        # Simulate slow/failing APIs
        for url in [
            "https://api.football-data.org/v4/competitions/PL",
            "https://fbref.com/en/comps/9/Premier-League-Stats",
            "https://api.sofascore.com/api/v1/unique-tournament/8/seasons",
            "https://api.sofascore.com/api/v1/sport/football/events/live",
        ]:
            responses.add(responses.GET, url, status=500)

        v = APIValidator()
        start = time.time()
        v.run_all()
        elapsed = time.time() - start

        # Even with retries, should complete in reasonable time
        # 4 endpoints * (1 + 2 retries) * ~backoff = should be < 30s
        assert elapsed < 30.0


# --- session/retry config ---

class TestSessionConfig:

    def test_session_has_user_agent_set(self):
        v = APIValidator()
        assert "User-Agent" in v.session.headers
        assert "Mozilla" in v.session.headers["User-Agent"]

    def test_retry_strategy_configured(self):
        v = APIValidator()
        adapter = v.session.get_adapter("https://example.com")
        retry = adapter.max_retries
        assert retry.total == 2
        # 429 should NOT be retried — it means "slow down"
        assert 429 not in retry.status_forcelist
        # 5xx server errors should be retried
        assert 500 in retry.status_forcelist
        assert 503 in retry.status_forcelist
