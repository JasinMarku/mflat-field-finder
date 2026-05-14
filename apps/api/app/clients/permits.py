"""Per-park permit CSV fetcher.

Endpoint:
    https://www.nycgovparks.org/permits/field-and-court/issued/{park_id}/csv

The CSV columns are: Start, End, Field, Sport or Event Type, Event Name,
Organization, Event Status. Dates look like ``3/20/2026 6:00 p.m.``;
``a.m.``/``p.m.`` must be normalized before parsing.

Politeness controls:
- Concurrency cap (asyncio.Semaphore)
- Minimum interval between requests (rate lock)
- 6-hour TTL cache per park
- 3 retry attempts with exponential backoff on 5xx and transport errors
- Realistic User-Agent and Referer headers

Fixture fallback: the upstream sits behind CloudFront, which 403s some
cloud egress IPs. When a live fetch fails, we fall back to a bundled
sample CSV so the demo stays functional even from a blocked host.
"""

from __future__ import annotations

import asyncio
import csv
import io
import logging
import time
from datetime import datetime
from pathlib import Path

import httpx
from dateutil import parser as dateparser

from app.cache import TTLCache
from app.config import Settings
from app.models import Permit


logger = logging.getLogger(__name__)

_CACHE_NAMESPACE = "permits_by_park"


def _parse_dt(s: str) -> datetime:
    cleaned = s.replace("a.m.", "AM").replace("p.m.", "PM")
    return dateparser.parse(cleaned)


def parse_permits_csv(csv_text: str, park_id: str) -> list[Permit]:
    """Parse a permit CSV body for a single park into Permit models."""
    permits: list[Permit] = []
    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        try:
            permits.append(
                Permit(
                    park_id=park_id,
                    field_name=row["Field"].strip(),
                    start=_parse_dt(row["Start"]),
                    end=_parse_dt(row["End"]),
                    sport_or_event=row.get("Sport or Event Type", "").strip(),
                    event_name=row.get("Event Name", "").strip(),
                    organization=row.get("Organization", "").strip(),
                    status=row.get("Event Status", "Approved").strip() or "Approved",
                )
            )
        except (KeyError, ValueError) as exc:
            logger.debug("Skipping malformed permit row for %s: %s", park_id, exc)
            continue
    return permits


class PermitClient:
    def __init__(self, settings: Settings, cache: TTLCache) -> None:
        self.settings = settings
        self.cache = cache
        self._semaphore = asyncio.Semaphore(settings.scrape_max_concurrency)
        self._last_request_at: float = 0.0
        self._rate_lock = asyncio.Lock()

    async def get_permits_for_parks(
        self, park_ids: list[str]
    ) -> tuple[dict[str, list[Permit]], dict[str, str]]:
        results = await asyncio.gather(
            *(self._get_permits_for_park(pid) for pid in park_ids)
        )
        permits_by_park: dict[str, list[Permit]] = {}
        sources_by_park: dict[str, str] = {}
        for park_id, (permits, source) in zip(park_ids, results):
            permits_by_park[park_id] = permits
            sources_by_park[park_id] = source
        return permits_by_park, sources_by_park

    async def _get_permits_for_park(self, park_id: str) -> tuple[list[Permit], str]:
        cached = self.cache.get(
            _CACHE_NAMESPACE,
            park_id,
            ttl_seconds=self.settings.permits_cache_ttl,
        )
        if cached is not None:
            return [Permit.model_validate(item) for item in cached], "cache"

        if self.settings.data_mode == "fixtures":
            permits = self._load_fixture(park_id)
            self.cache.set(
                _CACHE_NAMESPACE,
                park_id,
                [p.model_dump(mode="json") for p in permits],
            )
            return permits, "fixture"

        try:
            csv_text = await self._fetch_csv_polite(park_id)
            permits = parse_permits_csv(csv_text, park_id)
            self.cache.set(
                _CACHE_NAMESPACE,
                park_id,
                [p.model_dump(mode="json") for p in permits],
            )
            return permits, "live"
        except Exception as exc:  # network, HTTP, parse - any live-path failure
            logger.warning("Live fetch failed for %s (%s); trying fixture", park_id, exc)
            fallback = self._load_fixture(park_id)
            if fallback:
                return fallback, "fixture"
            return [], "error"

    async def _fetch_csv_polite(self, park_id: str) -> str:
        async with self._semaphore:
            await self._wait_for_min_interval()
            url = self.settings.permits_csv_url_template.format(park_id=park_id)
            headers = {
                "User-Agent": self.settings.user_agent,
                "Accept": "text/csv,text/plain,*/*",
                "Referer": f"{self.settings.nyc_parks_base_url}/permits/field-and-court/map",
            }
            return await self._fetch_with_retries(url, headers)

    async def _fetch_with_retries(
        self, url: str, headers: dict[str, str], max_attempts: int = 3
    ) -> str:
        last_exc: Exception | None = None
        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    return response.text
                except httpx.HTTPStatusError as exc:
                    status = exc.response.status_code
                    if 400 <= status < 500:
                        raise
                    last_exc = exc
                    logger.warning(
                        "Attempt %d for %s failed with %d", attempt, url, status
                    )
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_exc = exc
                    logger.warning("Attempt %d for %s transport error: %s", attempt, url, exc)
                if attempt < max_attempts:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
        assert last_exc is not None
        raise last_exc

    async def _wait_for_min_interval(self) -> None:
        async with self._rate_lock:
            now = time.monotonic()
            elapsed_ms = (now - self._last_request_at) * 1000.0
            min_ms = self.settings.scrape_min_interval_ms
            if elapsed_ms < min_ms:
                await asyncio.sleep((min_ms - elapsed_ms) / 1000.0)
            self._last_request_at = time.monotonic()

    def _load_fixture(self, park_id: str) -> list[Permit]:
        candidates = [
            Path(self.settings.fixtures_dir) / f"{park_id}.csv",
            Path(self.settings.fixtures_dir) / "sample_permits.csv",
        ]
        for path in candidates:
            if not path.exists():
                continue
            try:
                text = path.read_text(encoding="utf-8")
                permits = parse_permits_csv(text, park_id)
                logger.info("Loaded %d permits for %s from fixture %s", len(permits), park_id, path)
                return permits
            except OSError as exc:
                logger.warning("Failed to read fixture %s: %s", path, exc)
                continue
        logger.warning("No fixture available for park %s", park_id)
        return []
