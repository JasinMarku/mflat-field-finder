"""Socrata facility catalog client.

Fetches the qnem-b8re dataset, filters to active rows server-side,
normalizes each row to a :class:`Facility`, and caches the result.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.cache import TTLCache
from app.config import Settings
from app.domain.sports import sports_from_catalog_row
from app.models import Borough, Facility


logger = logging.getLogger(__name__)

_CACHE_NAMESPACE = "facility_catalog"
_CACHE_KEY = "all"
_PAGE_SIZE = 1000


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}
    return False


class SocrataClient:
    def __init__(self, settings: Settings, cache: TTLCache) -> None:
        self.settings = settings
        self.cache = cache

    async def get_all_facilities(self, force_refresh: bool = False) -> list[Facility]:
        if not force_refresh:
            cached = self.cache.get(
                _CACHE_NAMESPACE,
                _CACHE_KEY,
                ttl_seconds=self.settings.catalog_cache_ttl,
            )
            if cached is not None:
                logger.info("Catalog cache hit (%d facilities)", len(cached))
                return [Facility.model_validate(item) for item in cached]

        logger.info("Fetching facility catalog from Socrata")
        rows = await self._fetch_all_rows()
        facilities = [f for f in (self._row_to_facility(r) for r in rows) if f is not None]
        self.cache.set(
            _CACHE_NAMESPACE,
            _CACHE_KEY,
            [f.model_dump(mode="json") for f in facilities],
        )
        logger.info("Cached %d facilities (from %d rows)", len(facilities), len(rows))
        return facilities

    async def _fetch_all_rows(self) -> list[dict]:
        url = self.settings.socrata_dataset_url
        headers = {"User-Agent": self.settings.user_agent}
        all_rows: list[dict] = []
        offset = 0
        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            headers=headers,
        ) as client:
            while True:
                params = {
                    "$where": "featurestatus='Active'",
                    "$limit": _PAGE_SIZE,
                    "$offset": offset,
                }
                response = await client.get(url, params=params)
                response.raise_for_status()
                page = response.json()
                all_rows.extend(page)
                logger.debug("Fetched page offset=%d size=%d", offset, len(page))
                if len(page) < _PAGE_SIZE:
                    break
                offset += _PAGE_SIZE
        return all_rows

    @staticmethod
    def _row_to_facility(row: dict) -> Optional[Facility]:
        park_id = row.get("gispropnum")
        if not park_id:
            return None
        sports = sports_from_catalog_row(row)
        if not sports:
            return None
        borough = Borough.from_code(row.get("borough"))
        field_number = row.get("field_number") or "?"
        primary_sport = row.get("primary_sport") or "FIELD"
        facility_id = f"{park_id}-{primary_sport}-{field_number}"
        field_label = f"{primary_sport.title()} {field_number}"
        is_lighted = _truthy(row.get("field_lighted"))
        is_active = row.get("featurestatus", "Active") == "Active"
        return Facility(
            facility_id=facility_id,
            park_id=park_id,
            borough=borough,
            field_label=field_label,
            sports=sports,
            surface_type=row.get("surface_type"),
            is_lighted=is_lighted,
            is_active=is_active,
        )
