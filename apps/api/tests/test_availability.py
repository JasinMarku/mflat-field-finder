"""Tests for the availability algorithm."""

from __future__ import annotations

from datetime import datetime, time

from app.domain.availability import compute_free_slots
from app.models import Permit


def _p(
    field: str,
    start_iso: str,
    end_iso: str,
    sport: str = " Soccer - Non Regulation",
) -> Permit:
    return Permit(
        park_id="TEST",
        field_name=field,
        start=datetime.fromisoformat(start_iso),
        end=datetime.fromisoformat(end_iso),
        sport_or_event=sport,
    )


DAY_START = time(7, 0)
DAY_END = time(22, 0)


def test_no_permits_returns_full_operating_windows() -> None:
    free, busy = compute_free_slots(
        permits=[],
        range_start=datetime(2026, 5, 18),
        range_end=datetime(2026, 5, 20),
        day_start=DAY_START,
        day_end=DAY_END,
    )
    assert len(free) == 2
    assert all(w.duration_minutes == 15 * 60 for w in free)
    assert sum(w.duration_minutes for w in free) == 1800
    assert busy == []


def test_single_permit_in_middle_of_day_splits_window() -> None:
    permits = [_p("F1", "2026-05-18T12:00:00", "2026-05-18T14:00:00")]
    free, busy = compute_free_slots(
        permits,
        datetime(2026, 5, 18),
        datetime(2026, 5, 19),
        DAY_START,
        DAY_END,
    )
    assert len(free) == 2
    assert [w.duration_minutes for w in free] == [300, 480]
    assert len(busy) == 1
    assert busy[0].duration_minutes == 120


def test_overlapping_permits_are_merged() -> None:
    permits = [
        _p("F1", "2026-05-18T12:00:00", "2026-05-18T14:00:00"),
        _p("F1", "2026-05-18T13:30:00", "2026-05-18T15:00:00"),
    ]
    free, busy = compute_free_slots(
        permits,
        datetime(2026, 5, 18),
        datetime(2026, 5, 19),
        DAY_START,
        DAY_END,
    )
    assert sorted(w.duration_minutes for w in free) == [300, 420]
    assert len(busy) == 1
    assert busy[0].duration_minutes == 180


def test_permit_outside_operating_hours_does_not_affect_free_slots() -> None:
    permits = [_p("F1", "2026-05-18T02:00:00", "2026-05-18T04:00:00")]
    free, busy = compute_free_slots(
        permits,
        datetime(2026, 5, 18),
        datetime(2026, 5, 19),
        DAY_START,
        DAY_END,
    )
    assert len(free) == 1
    assert free[0].duration_minutes == 15 * 60
    assert busy == []


def test_full_closure_blocks_entire_window() -> None:
    permits = [
        _p(
            "F1",
            "2025-01-01T00:00:00",
            "2027-12-31T23:55:00",
            sport="Full Closure",
        )
    ]
    free, busy = compute_free_slots(
        permits,
        datetime(2026, 5, 18),
        datetime(2026, 5, 25),
        DAY_START,
        DAY_END,
    )
    assert free == []
    assert len(busy) == 7
    assert all(w.duration_minutes == 15 * 60 for w in busy)


def test_min_slot_minutes_filters_short_gaps() -> None:
    permits = [
        _p("F1", "2026-05-18T07:00:00", "2026-05-18T07:45:00"),
        _p("F1", "2026-05-18T08:00:00", "2026-05-18T22:00:00"),
    ]
    free, _busy = compute_free_slots(
        permits,
        datetime(2026, 5, 18),
        datetime(2026, 5, 19),
        DAY_START,
        DAY_END,
        min_slot_minutes=60,
    )
    assert free == []


def test_permit_spans_midnight_into_next_day() -> None:
    permits = [_p("F1", "2026-05-18T22:00:00", "2026-05-19T06:00:00")]
    free, busy = compute_free_slots(
        permits,
        datetime(2026, 5, 18),
        datetime(2026, 5, 20),
        DAY_START,
        DAY_END,
    )
    assert len(free) == 2
    assert all(w.duration_minutes == 15 * 60 for w in free)
    assert busy == []


def test_adjacent_permits_no_gap() -> None:
    permits = [
        _p("F1", "2026-05-18T08:00:00", "2026-05-18T10:00:00"),
        _p("F1", "2026-05-18T10:00:00", "2026-05-18T12:00:00"),
    ]
    free, busy = compute_free_slots(
        permits,
        datetime(2026, 5, 18),
        datetime(2026, 5, 19),
        DAY_START,
        DAY_END,
    )
    assert sorted(w.duration_minutes for w in free) == [60, 600]
    assert len(busy) == 1
    assert busy[0].duration_minutes == 240


def test_range_partial_day_at_edges() -> None:
    free, busy = compute_free_slots(
        permits=[],
        range_start=datetime(2026, 5, 18, 14, 0),
        range_end=datetime(2026, 5, 19, 10, 0),
        day_start=DAY_START,
        day_end=DAY_END,
    )
    assert sorted(w.duration_minutes for w in free) == [180, 480]
    assert busy == []


def test_returns_busy_slots_clipped_to_operating_hours() -> None:
    permits = [_p("F1", "2026-05-18T06:00:00", "2026-05-18T12:00:00")]
    _free, busy = compute_free_slots(
        permits,
        datetime(2026, 5, 18),
        datetime(2026, 5, 19),
        DAY_START,
        DAY_END,
    )
    assert len(busy) == 1
    assert busy[0].start == datetime(2026, 5, 18, 7, 0)
    assert busy[0].end == datetime(2026, 5, 18, 12, 0)
    assert busy[0].duration_minutes == 300
