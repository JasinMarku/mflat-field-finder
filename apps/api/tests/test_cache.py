"""Tests for the SQLite TTL cache."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.cache import TTLCache


def test_set_then_get_returns_payload(tmp_path: Path) -> None:
    cache = TTLCache(tmp_path / "cache.sqlite")
    cache.set("ns", "k", {"hello": "world"})
    assert cache.get("ns", "k", ttl_seconds=60) == {"hello": "world"}


def test_get_missing_key_returns_none(tmp_path: Path) -> None:
    cache = TTLCache(tmp_path / "cache.sqlite")
    assert cache.get("ns", "missing", ttl_seconds=60) is None


def test_get_expired_ttl_returns_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = TTLCache(tmp_path / "cache.sqlite")
    # Freeze "now" so set() records a known fetched_at.
    monkeypatch.setattr("app.cache.time.time", lambda: 1_000.0)
    cache.set("ns", "k", [1, 2, 3])
    # Advance the clock past the TTL.
    monkeypatch.setattr("app.cache.time.time", lambda: 1_100.0)
    assert cache.get("ns", "k", ttl_seconds=50) is None
    # Within TTL it still hits.
    assert cache.get("ns", "k", ttl_seconds=200) == [1, 2, 3]


def test_purge_namespace_removes_only_that_namespace(tmp_path: Path) -> None:
    cache = TTLCache(tmp_path / "cache.sqlite")
    cache.set("a", "k1", 1)
    cache.set("a", "k2", 2)
    cache.set("b", "k1", "keep")
    removed = cache.purge_namespace("a")
    assert removed == 2
    assert cache.get("a", "k1", ttl_seconds=60) is None
    assert cache.get("a", "k2", ttl_seconds=60) is None
    assert cache.get("b", "k1", ttl_seconds=60) == "keep"


def test_set_upserts_existing_key(tmp_path: Path) -> None:
    cache = TTLCache(tmp_path / "cache.sqlite")
    cache.set("ns", "k", "first")
    cache.set("ns", "k", "second")
    assert cache.get("ns", "k", ttl_seconds=60) == "second"
