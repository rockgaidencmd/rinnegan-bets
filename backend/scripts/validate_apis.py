#!/usr/bin/env python3
"""
Validation script to test all external APIs before using them.
Reports detailed response data for debugging and verification.

Features:
- Timeout: 5 seconds max per request (non-blocking)
- Retry: 2 attempts per endpoint (resilient)
- Detail: Headers, response size, structure validation
- Correct URLs based on actual API documentation
"""

import os
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional
from datetime import datetime


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class APIValidator:
    """Validates all external data sources with detailed reporting."""

    def __init__(self, football_data_key: Optional[str] = None):
        self.results = []
        self.football_data_key = football_data_key or os.environ.get("FOOTBALL_DATA_API_KEY")
        self.session = self._create_session_with_retry()

    def _create_session_with_retry(self) -> requests.Session:
        """Session with automatic retry on transient failures.

        Note: 429 (rate limit) is intentionally NOT retried — when an API
        says "slow down" we should report it, not hammer harder.
        """
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],  # 429 excluded on purpose
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": USER_AGENT})
        return session

    def _get_with_details(
        self, url: str, headers: Optional[Dict] = None, timeout: float = 5.0
    ) -> Dict[str, Any]:
        """GET request with detailed response info extraction."""
        try:
            response = self.session.get(
                url,
                headers=headers or {},
                timeout=timeout,
                allow_redirects=True
            )
            content_sample = response.text[:300] if response.text else ""
            return {
                "status_code": response.status_code,
                "response_size_bytes": len(response.content),
                "content_type": response.headers.get("Content-Type", "unknown"),
                "sample": content_sample,
                "elapsed_ms": int(response.elapsed.total_seconds() * 1000),
                "error": None
            }
        except requests.Timeout:
            return {"status_code": None, "error": f"TIMEOUT (>{timeout}s)", "elapsed_ms": int(timeout * 1000)}
        except requests.ConnectionError as e:
            return {"status_code": None, "error": f"CONNECTION_ERROR: {str(e)[:80]}", "elapsed_ms": 0}
        except Exception as e:
            return {"status_code": None, "error": f"ERROR: {str(e)[:80]}", "elapsed_ms": 0}

    def test_football_data_org(self) -> Dict[str, Any]:
        """
        Football-Data.org v4 API.
        Free tier: 10 calls/min, requires free API key.
        Docs: https://www.football-data.org/documentation/api
        """
        url = "https://api.football-data.org/v4/competitions/PL"
        headers = {}
        if self.football_data_key:
            headers["X-Auth-Token"] = self.football_data_key

        response = self._get_with_details(url, headers=headers, timeout=5)
        sc = response.get("status_code")

        if sc == 200:
            status, result = "✅", "Premier League data accessible"
        elif sc == 403 and not self.football_data_key:
            status, result = "⚠️", "Needs FOOTBALL_DATA_API_KEY (free at football-data.org/client/register)"
        elif sc == 429:
            status, result = "⚠️", "Rate limited (10/min on free tier)"
        elif sc:
            status, result = "⚠️", f"HTTP {sc}"
        else:
            status, result = "❌", response.get("error", "Unknown")

        return {
            "status": status,
            "name": "Football-Data.org v4",
            "result": result,
            "detail": f"{response.get('response_size_bytes', 0)} bytes in {response.get('elapsed_ms', 0)}ms",
            "raw": response,
        }

    def test_fbref(self) -> Dict[str, Any]:
        """
        FBref (Sports Reference) - web scraping for xG/xA.
        No API, scrape HTML. Rate limit: be respectful (1 req/3sec).
        Docs: https://fbref.com/en/comps/
        """
        # Top of competition page is lightweight; squad pages are heavier
        url = "https://fbref.com/en/comps/9/Premier-League-Stats"
        response = self._get_with_details(url, timeout=5)
        sc = response.get("status_code")

        if sc == 200:
            has_xg = "xG" in response.get("sample", "")
            status = "✅"
            result = "Scrapeable" + (" (xG keyword found)" if has_xg else "")
        elif sc == 403:
            status, result = "⚠️", "Blocked (might need different User-Agent or IP)"
        elif sc == 429:
            status, result = "⚠️", "Rate limited (slow down requests)"
        elif sc:
            status, result = "⚠️", f"HTTP {sc}"
        else:
            status, result = "⚠️", response.get("error", "Unknown")

        return {
            "status": status,
            "name": "FBref (Sports Reference)",
            "result": result,
            "detail": f"{response.get('response_size_bytes', 0)} bytes in {response.get('elapsed_ms', 0)}ms",
            "raw": response,
        }

    def test_sofascore(self) -> Dict[str, Any]:
        """
        SofaScore unofficial API.
        Endpoint patterns observed in browser DevTools.
        Tournament 8 = Premier League. Use /seasons/ first to find current.
        """
        url = "https://api.sofascore.com/api/v1/unique-tournament/8/seasons"
        response = self._get_with_details(url, timeout=5)
        sc = response.get("status_code")

        if sc == 200:
            status, result = "✅", "Unofficial API accessible"
        elif sc == 403:
            status, result = "⚠️", "Cloudflare blocked (try different User-Agent)"
        elif sc:
            status, result = "⚠️", f"HTTP {sc}"
        else:
            status, result = "❌", response.get("error", "Unknown")

        return {
            "status": status,
            "name": "SofaScore (seasons)",
            "result": result,
            "detail": f"{response.get('response_size_bytes', 0)} bytes in {response.get('elapsed_ms', 0)}ms",
            "raw": response,
        }

    def test_live_data(self) -> Dict[str, Any]:
        """SofaScore live events endpoint."""
        url = "https://api.sofascore.com/api/v1/sport/football/events/live"
        response = self._get_with_details(url, timeout=5)
        sc = response.get("status_code")

        if sc == 200:
            status, result = "✅", "Live events accessible"
        elif sc == 429:
            status, result = "⚠️", "Rate limited"
        elif sc:
            status, result = "⚠️", f"HTTP {sc}"
        else:
            status, result = "⚠️", response.get("error", "Unknown")

        return {
            "status": status,
            "name": "SofaScore Live",
            "result": result,
            "detail": f"{response.get('response_size_bytes', 0)} bytes in {response.get('elapsed_ms', 0)}ms",
            "raw": response,
        }

    def run_all(self):
        """Run all validations and print report."""
        print("\n" + "=" * 80)
        print("RINNEGAN BETS — API VALIDATION REPORT")
        print(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
        if not self.football_data_key:
            print("ℹ️  No FOOTBALL_DATA_API_KEY set — Football-Data will likely 403")
        print("=" * 80 + "\n")

        tests = [
            self.test_football_data_org,
            self.test_fbref,
            self.test_sofascore,
            self.test_live_data,
        ]

        for test_fn in tests:
            result = test_fn()
            self.results.append(result)
            print(f"{result['status']} {result['name']}")
            print(f"   Result: {result['result']}")
            print(f"   Detail: {result['detail']}\n")

        passed = sum(1 for r in self.results if r["status"] == "✅")
        warnings = sum(1 for r in self.results if r["status"] == "⚠️")
        failed = sum(1 for r in self.results if r["status"] == "❌")

        print("=" * 80)
        print(f"Summary: {passed} ✅ | {warnings} ⚠️  | {failed} ❌")
        if passed >= 2:
            print("✅ At least 2 sources working — data pipeline is viable")
        elif passed >= 1:
            print("⚠️  Only 1 source working — coverage limited")
        else:
            print("❌ No sources working — check network/keys")
        print("=" * 80 + "\n")

        return self.results


if __name__ == "__main__":
    validator = APIValidator()
    results = validator.run_all()
    # Exit non-zero only if ALL failed (warnings are tolerable)
    sys.exit(1 if all(r["status"] == "❌" for r in results) else 0)
