"""Availability endpoint. Ties together catalog, permits, and the algorithm."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from app.domain.availability import compute_free_slots
from app.domain.sports import sport_from_permit_text
from app.models import (
    AvailabilityResponse,
    Borough,
    Facility,
    FacilityAvailability,
    Permit,
    PermitDensity,
    Sport,
)


router = APIRouter(prefix="/api", tags=["availability"])


_MAX_RANGE_DAYS = 31


def _aggregate_cache_status(sources: list[str]) -> str:
    unique = set(sources)
    if not unique:
        return "unknown"
    if unique == {"cache"}:
        return "cache"
    if "live" in unique:
        return "live"
    if "fixture" in unique:
        return "fixture"
    return "mixed"


@router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(
    request: Request,
    sport: Sport,
    date_from: datetime = Query(..., alias="from"),
    date_to: datetime = Query(..., alias="to"),
    borough: Optional[Borough] = None,
    min_slot_minutes: int = Query(60, ge=0),
) -> AvailabilityResponse:
    if date_from >= date_to:
        raise HTTPException(status_code=400, detail="'from' must be before 'to'")
    if (date_to - date_from) > timedelta(days=_MAX_RANGE_DAYS):
        raise HTTPException(
            status_code=400, detail=f"Date range cannot exceed {_MAX_RANGE_DAYS} days"
        )

    settings = request.app.state.settings
    socrata = request.app.state.socrata_client
    permit_client = request.app.state.permit_client

    facilities: list[Facility] = await socrata.get_all_facilities()
    matching = [f for f in facilities if sport in f.sports]
    if borough is not None:
        matching = [f for f in matching if f.borough == borough]

    if not matching:
        return AvailabilityResponse(
            sport=sport,
            range_start=date_from,
            range_end=date_to,
            facilities=[],
            total_facilities=0,
            total_free_minutes=0,
            cache_status="unknown",
            permit_density=PermitDensity.NONE,
        )

    park_ids = sorted({f.park_id for f in matching})
    borough_by_park: dict[str, Borough] = {}
    for facility in matching:
        borough_by_park.setdefault(facility.park_id, facility.borough)

    permits_by_park, sources_by_park = await permit_client.get_permits_for_parks(park_ids)

    rows: list[FacilityAvailability] = []

    for park_id in park_ids:
        park_permits = permits_by_park.get(park_id, [])
        relevant: list[Permit] = [
            p
            for p in park_permits
            if sport_from_permit_text(p.sport_or_event) == sport or p.is_full_closure
        ]

        if not relevant:
            # No relevant permits at this park in the upstream feed. Fall back
            # to catalog facilities for this park: each is 100% available.
            for facility in (f for f in matching if f.park_id == park_id):
                free, busy = compute_free_slots(
                    [],
                    date_from,
                    date_to,
                    settings.default_day_start,
                    settings.default_day_end,
                    min_slot_minutes,
                )
                rows.append(
                    FacilityAvailability(
                        facility=facility,
                        free_slots=free,
                        permitted_slots=busy,
                        total_free_minutes=sum(w.duration_minutes for w in free),
                        has_full_closure=False,
                    )
                )
            continue

        by_field: dict[str, list[Permit]] = defaultdict(list)
        for permit in relevant:
            by_field[permit.field_name].append(permit)

        park_borough = borough_by_park.get(park_id, Borough.UNKNOWN)
        for field_name, field_permits in by_field.items():
            free, busy = compute_free_slots(
                field_permits,
                date_from,
                date_to,
                settings.default_day_start,
                settings.default_day_end,
                min_slot_minutes,
            )
            synthetic = Facility(
                facility_id=f"{park_id}::{field_name}",
                park_id=park_id,
                borough=park_borough,
                field_label=field_name,
                sports=frozenset({sport}),
                surface_type=None,
                is_lighted=False,
                is_active=True,
            )
            rows.append(
                FacilityAvailability(
                    facility=synthetic,
                    free_slots=free,
                    permitted_slots=busy,
                    total_free_minutes=sum(w.duration_minutes for w in free),
                    has_full_closure=any(
                        p.is_full_closure
                        and p.start < date_to
                        and p.end > date_from
                        for p in field_permits
                    ),
                )
            )

    rows.sort(key=lambda r: r.total_free_minutes, reverse=True)

    cache_status = _aggregate_cache_status(list(sources_by_park.values()))

    facilities_with_permits = sum(1 for fa in rows if fa.permitted_slots)
    total = len(rows)
    if total == 0 or facilities_with_permits == 0:
        density = PermitDensity.NONE
    elif facilities_with_permits / total < 0.2:
        density = PermitDensity.LOW
    else:
        density = PermitDensity.HIGH

    return AvailabilityResponse(
        sport=sport,
        range_start=date_from,
        range_end=date_to,
        facilities=rows,
        total_facilities=len(rows),
        total_free_minutes=sum(r.total_free_minutes for r in rows),
        cache_status=cache_status,
        permit_density=density,
    )


__all__ = ["router"]
