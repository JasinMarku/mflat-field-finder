"""Facility catalog endpoint."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request

from app.models import Borough, Facility, Sport


router = APIRouter(prefix="/api", tags=["facilities"])


@router.get("/facilities", response_model=list[Facility])
async def list_facilities(
    request: Request,
    sport: Sport,
    borough: Optional[Borough] = None,
) -> list[Facility]:
    facilities = await request.app.state.socrata_client.get_all_facilities()
    matching = [f for f in facilities if sport in f.sports]
    if borough is not None:
        matching = [f for f in matching if f.borough == borough]
    matching.sort(key=lambda f: (f.park_id, f.facility_id))
    return matching
