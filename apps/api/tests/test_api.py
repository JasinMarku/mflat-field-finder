"""HTTP-level tests using TestClient. Runs in fixture mode, no network."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATA_MODE", "fixtures")
    monkeypatch.setenv("CACHE_DB_PATH", str(tmp_path / "cache.sqlite"))

    # Reset the lru_cache on get_settings so the new env is picked up,
    # and reload main so the app is built against fresh settings.
    from app import config

    config.get_settings.cache_clear()

    from app import main

    main_reloaded = importlib.reload(main)
    # Use the context-manager form so the lifespan runs and app.state is
    # populated before any request hits the routes.
    with TestClient(main_reloaded.app) as test_client:
        yield test_client


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_sports_endpoint_returns_canonical_list(client: TestClient) -> None:
    response = client.get("/api/sports")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0
    for item in body:
        assert {"code", "label", "facility_count"} <= item.keys()
    codes = {item["code"] for item in body}
    assert "soccer" in codes


def test_facilities_endpoint_filters_by_sport(client: TestClient) -> None:
    response = client.get("/api/facilities", params={"sport": "soccer"})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0
    for facility in body:
        assert "soccer" in facility["sports"]


def test_availability_endpoint_basic_query(client: TestClient) -> None:
    response = client.get(
        "/api/availability",
        params={
            "sport": "soccer",
            "from": "2026-05-18",
            "to": "2026-05-25",
            "min_slot_minutes": 60,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sport"] == "soccer"
    assert body["range_start"].startswith("2026-05-18")
    assert body["range_end"].startswith("2026-05-25")
    assert isinstance(body["facilities"], list)
    assert body["total_facilities"] == len(body["facilities"])

    computed_total = 0
    for row in body["facilities"]:
        slot_total = sum(
            int(
                (
                    _dt(slot["end"]) - _dt(slot["start"])
                ).total_seconds()
                // 60
            )
            for slot in row["free_slots"]
        )
        assert row["total_free_minutes"] == slot_total
        computed_total += slot_total
    assert body["total_free_minutes"] == computed_total


def test_availability_endpoint_validates_date_range(client: TestClient) -> None:
    too_long = client.get(
        "/api/availability",
        params={"sport": "soccer", "from": "2026-05-01", "to": "2026-07-01"},
    )
    assert too_long.status_code == 400

    inverted = client.get(
        "/api/availability",
        params={"sport": "soccer", "from": "2026-05-20", "to": "2026-05-19"},
    )
    assert inverted.status_code == 400

    equal = client.get(
        "/api/availability",
        params={"sport": "soccer", "from": "2026-05-20", "to": "2026-05-20"},
    )
    assert equal.status_code == 400


def _dt(iso: str):
    from datetime import datetime

    return datetime.fromisoformat(iso)
