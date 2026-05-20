"""Base HTTP client with retry + timeout + cache integration.

All fetchers inherit from this to share session config and cache patterns.
"""

from datetime import timedelta
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from data.cache import CacheService, make_cache_key


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class FetchError(Exception):
    """Raised when an HTTP fetch fails permanently (after retries)."""


class BaseFetcher:
    """Shared HTTP session + cache pattern for all data sources."""

    name: str = "base"  # Subclasses override (e.g., "fd", "sofa")
    default_timeout: float = 5.0

    def __init__(self, cache: CacheService):
        self._cache = cache
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        """Session with retry on 5xx, 5s timeout, browser-like User-Agent.

        Note: 429 is NOT retried — when an API says "slow down" we respect it.
        """
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": USER_AGENT})
        return session

    def _cache_key(self, *parts: Any) -> str:
        """Build cache key namespaced by fetcher name."""
        return make_cache_key(self.name, *parts)

    def _fetch_json(
        self,
        url: str,
        cache_key: str,
        ttl: timedelta | None = None,
        headers: dict | None = None,
    ) -> dict:
        """Read-through fetch: cache → HTTP → cache → return.

        Raises FetchError on permanent failures.
        """
        # 1. Try cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # 2. Fetch from network
        try:
            response = self._session.get(
                url,
                headers=headers or {},
                timeout=self.default_timeout,
            )
        except requests.Timeout:
            raise FetchError(f"Timeout fetching {url}")
        except requests.ConnectionError as e:
            raise FetchError(f"Connection error fetching {url}: {e}")

        if response.status_code != 200:
            raise FetchError(
                f"HTTP {response.status_code} fetching {url}: {response.text[:200]}"
            )

        try:
            payload = response.json()
        except ValueError as e:
            raise FetchError(f"Invalid JSON from {url}: {e}")

        # 3. Cache the result
        self._cache.set(cache_key, payload, ttl=ttl)
        return payload
