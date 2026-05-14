"""Tests for permit CSV parsing and Permit.is_full_closure."""

from __future__ import annotations

from datetime import datetime

from app.clients.permits import parse_permits_csv
from app.models import Permit


GOOD_CSV = """Start,End,Field,Sport or Event Type,Event Name,Organization,Event Status
5/18/2026 6:00 p.m.,5/18/2026 8:00 p.m., Soccer 01, Soccer - Regulation,Spring Match,East Side FC,Approved
5/19/2026 9:00 a.m.,5/19/2026 11:00 a.m., Softball 01, Softball (Adult),League Game,Park Slope Softball,Approved
"""


def test_parse_permits_csv_basic() -> None:
    permits = parse_permits_csv(GOOD_CSV, "B073")
    assert len(permits) == 2
    first, second = permits
    assert first.park_id == "B073"
    assert first.field_name == "Soccer 01"
    assert first.sport_or_event == "Soccer - Regulation"
    assert first.start == datetime(2026, 5, 18, 18, 0)
    assert first.end == datetime(2026, 5, 18, 20, 0)
    assert first.organization == "East Side FC"
    assert second.start == datetime(2026, 5, 19, 9, 0)
    assert second.field_name == "Softball 01"


def test_parse_permits_csv_skips_malformed_rows() -> None:
    csv_text = """Start,End,Field,Sport or Event Type,Event Name,Organization,Event Status
not a date,also bad, Bad 01, Soccer,Bad Row,Nobody,Approved
5/20/2026 7:00 p.m.,5/20/2026 9:00 p.m., Soccer 02, Soccer - Regulation,Good Row,FC United,Approved
"""
    permits = parse_permits_csv(csv_text, "M028")
    assert len(permits) == 1
    assert permits[0].field_name == "Soccer 02"
    assert permits[0].start == datetime(2026, 5, 20, 19, 0)


def test_permit_is_full_closure() -> None:
    base = {
        "park_id": "M028",
        "field_name": "Soccer 03",
        "start": datetime(2026, 1, 1),
        "end": datetime(2027, 12, 31),
    }
    assert Permit(sport_or_event="Full Closure", **base).is_full_closure
    assert Permit(sport_or_event="FULL CLOSURE", **base).is_full_closure
    assert Permit(sport_or_event=" Full Closure - Renovation", **base).is_full_closure
    assert not Permit(sport_or_event=" Soccer - Non Regulation", **base).is_full_closure
    assert not Permit(sport_or_event="Soccer", **base).is_full_closure
