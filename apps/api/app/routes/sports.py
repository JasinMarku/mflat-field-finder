"""Sport listing endpoint."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.domain.sports import all_supported_sports, display_label
from app.models import Sport


router = APIRouter(prefix="/api", tags=["sports"])


class SportSummary(BaseModel):
    code: str
    label: str
    facility_count: int


@router.get("/sports", response_model=list[SportSummary])
async def list_sports(request: Request) -> list[SportSummary]:
    facilities = await request.app.state.socrata_client.get_all_facilities()
    counter: Counter[Sport] = Counter()
    for facility in facilities:
        for sport in facility.sports:
            counter[sport] += 1

    summaries = [
        SportSummary(
            code=sport.value,
            label=display_label(sport),
            facility_count=counter.get(sport, 0),
        )
        for sport in all_supported_sports()
    ]
    summaries.sort(key=lambda s: s.facility_count, reverse=True)
    return summaries
