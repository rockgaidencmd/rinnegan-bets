"""Tests for CacheService — verifies read-through pattern + TTL + UPSERT."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from data.cache import CacheService, make_cache_key
from db.base import Base
from db.models import DataCache


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


class TestCacheGet:

    def test_returns_none_when_key_missing(self, cache):
        assert cache.get("missing") is None

    def test_returns_value_when_key_present_and_fresh(self, cache):
        cache.set("k1", {"hello": "world"})
        assert cache.get("k1") == {"hello": "world"}

    def test_returns_none_when_entry_expired(self, cache, session):
        # Manually insert an expired entry
        now = datetime.now(timezone.utc)
        session.add(DataCache(
            key="old",
            payload={"stale": True},
            fetched_at=now - timedelta(days=2),
            expires_at=now - timedelta(days=1),
        ))
        session.commit()

        assert cache.get("old") is None


class TestCacheSet:

    def test_set_creates_new_entry(self, cache, session):
        cache.set("new_key", {"data": 123})

        row = session.get(DataCache, "new_key")
        assert row is not None
        assert row.payload == {"data": 123}

    def test_set_overwrites_existing_entry_atomically(self, cache, session):
        """UPSERT pattern: second set should replace first, not duplicate."""
        cache.set("k", {"v": 1})
        cache.set("k", {"v": 2})

        # Should still be only one row
        rows = session.execute(select(DataCache).where(DataCache.key == "k")).scalars().all()
        assert len(rows) == 1
        assert rows[0].payload == {"v": 2}

    def test_set_with_custom_ttl(self, cache, session):
        short_ttl = timedelta(seconds=10)
        cache.set("short", {"x": 1}, ttl=short_ttl)

        row = session.get(DataCache, "short")
        # Should expire ~10 seconds from now
        delta = (row.expires_at - row.fetched_at).total_seconds()
        assert 9 <= delta <= 11

    def test_set_default_ttl_is_24h(self, cache, session):
        cache.set("default_ttl", {"x": 1})

        row = session.get(DataCache, "default_ttl")
        delta = row.expires_at - row.fetched_at
        # Allow slight wiggle room
        assert timedelta(hours=23, minutes=59) <= delta <= timedelta(hours=24, minutes=1)

    def test_set_preserves_complex_nested_payload(self, cache):
        complex_payload = {
            "matches": [
                {"id": 1, "score": {"home": 2, "away": 1}, "xg": [1.5, 0.8]},
                {"id": 2, "stats": {"shots": [{"x": 0.5, "outcome": "goal"}]}},
            ],
            "metadata": {"fetched": True, "count": 2},
        }
        cache.set("complex", complex_payload)
        assert cache.get("complex") == complex_payload


class TestCacheInvalidate:

    def test_invalidate_returns_true_when_key_existed(self, cache):
        cache.set("existing", {"x": 1})
        assert cache.invalidate("existing") is True
        assert cache.get("existing") is None

    def test_invalidate_returns_false_when_key_missing(self, cache):
        assert cache.invalidate("never_existed") is False


class TestCacheSweep:

    def test_sweep_removes_expired_entries(self, cache, session):
        now = datetime.now(timezone.utc)
        # 2 expired, 1 fresh
        for i, expired in enumerate([True, True, False]):
            session.add(DataCache(
                key=f"k{i}",
                payload={"i": i},
                fetched_at=now - timedelta(days=1),
                expires_at=now - timedelta(hours=1) if expired else now + timedelta(hours=1),
            ))
        session.commit()

        deleted = cache.sweep()

        assert deleted == 2
        remaining = session.execute(select(DataCache)).scalars().all()
        assert len(remaining) == 1
        assert remaining[0].key == "k2"

    def test_sweep_returns_zero_when_nothing_expired(self, cache):
        cache.set("fresh1", {"x": 1})
        cache.set("fresh2", {"x": 2})
        assert cache.sweep() == 0


class TestMakeCacheKey:

    def test_joins_parts_with_colon(self):
        assert make_cache_key("a", "b", "c") == "a:b:c"

    def test_converts_non_strings(self):
        assert make_cache_key("teams", "PL", 123) == "teams:PL:123"

    def test_single_part(self):
        assert make_cache_key("solo") == "solo"
