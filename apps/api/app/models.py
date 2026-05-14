"""Domain models. Pure Pydantic v2, no logic beyond simple properties."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Borough(str, Enum):
    MANHATTAN = "M"
    BRONX = "X"
    BROOKLYN = "B"
    QUEENS = "Q"
    STATEN_ISLAND = "R"
    UNKNOWN = "?"

    @classmethod
    def from_code(cls, code: Optional[str]) -> "Borough":
        if code is None:
            return cls.UNKNOWN
        normalized = code.strip().upper()
        if not normalized:
            return cls.UNKNOWN
        for member in cls:
            if member.value == normalized:
                return member
        return cls.UNKNOWN

    @property
    def label(self) -> str:
        return {
            Borough.MANHATTAN: "Manhattan",
            Borough.BRONX: "Bronx",
            Borough.BROOKLYN: "Brooklyn",
            Borough.QUEENS: "Queens",
            Borough.STATEN_ISLAND: "Staten Island",
            Borough.UNKNOWN: "Unknown",
        }[self]


class Sport(str, Enum):
    SOCCER = "soccer"
    BASEBALL = "baseball"
    SOFTBALL = "softball"
    FOOTBALL = "football"
    FLAG_FOOTBALL = "flag_football"
    BASKETBALL = "basketball"
    VOLLEYBALL = "volleyball"
    TENNIS = "tennis"
    HANDBALL = "handball"
    CRICKET = "cricket"
    LACROSSE = "lacrosse"
    RUGBY = "rugby"
    HOCKEY = "hockey"
    FRISBEE = "frisbee"
    PICKLEBALL = "pickleball"
    BOCCE = "bocce"
    KICKBALL = "kickball"
    NETBALL = "netball"
    OTHER = "other"


class Facility(BaseModel):
    model_config = ConfigDict(frozen=True)

    facility_id: str
    park_id: str
    borough: Borough
    field_label: str
    sports: frozenset[Sport]
    surface_type: Optional[str] = None
    is_lighted: bool = False
    is_active: bool = True


class Permit(BaseModel):
    model_config = ConfigDict(frozen=True)

    park_id: str
    field_name: str
    start: datetime
    end: datetime
    sport_or_event: str
    event_name: str = ""
    organization: str = ""
    status: str = "Approved"

    @property
    def is_full_closure(self) -> bool:
        return "full closure" in self.sport_or_event.lower()


class TimeWindow(BaseModel):
    model_config = ConfigDict(frozen=True)

    start: datetime
    end: datetime

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() // 60)


class FacilityAvailability(BaseModel):
    model_config = ConfigDict(frozen=True)

    facility: Facility
    free_slots: list[TimeWindow]
    permitted_slots: list[TimeWindow]
    total_free_minutes: int
    has_full_closure: bool = False


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    sport: Sport
    range_start: datetime
    range_end: datetime
    facilities: list[FacilityAvailability]
    total_facilities: int
    total_free_minutes: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    cache_status: str = "unknown"
