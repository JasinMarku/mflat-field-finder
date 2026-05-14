"""Availability algorithm.

This is the only real algorithm in the codebase. Given a list of permits
(busy blocks) on a single field, a date range, and operating hours per
day, return the free :class:`TimeWindow` s.

Approach: for each day in the range, build the operating window, then
subtract the merged permits that intersect that day. Standard interval
arithmetic.

The busy slots we return are clipped to the daily operating window. A
Full Closure permit spanning years would otherwise produce a single
multi-year block, which breaks calendar UI rendering and over-reports
the closure inside our query range.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Iterable

from app.models import Permit, TimeWindow


def _merge_intervals(
    intervals: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda iv: iv[0])
    merged: list[tuple[datetime, datetime]] = [sorted_intervals[0]]
    for start, end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _subtract(
    window: tuple[datetime, datetime],
    blocks: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    win_start, win_end = window
    out: list[tuple[datetime, datetime]] = []
    cursor = win_start
    for block_start, block_end in blocks:
        if block_end <= cursor:
            continue
        if block_start >= win_end:
            break
        if block_start > cursor:
            out.append((cursor, block_start))
        cursor = max(cursor, block_end)
        if cursor >= win_end:
            break
    if cursor < win_end:
        out.append((cursor, win_end))
    return out


def _daterange(start: date, end_exclusive: date) -> Iterable[date]:
    current = start
    while current < end_exclusive:
        yield current
        current += timedelta(days=1)


def compute_free_slots(
    permits: list[Permit],
    range_start: datetime,
    range_end: datetime,
    day_start: time,
    day_end: time,
    min_slot_minutes: int = 30,
) -> tuple[list[TimeWindow], list[TimeWindow]]:
    """Return (free_slots, permitted_slots) for one field over the range.

    Permitted slots are clipped to the daily operating window so a multi-year
    Full Closure does not collapse into one unreadable block.
    """
    if range_end <= range_start:
        return [], []

    daily_windows: list[tuple[datetime, datetime]] = []
    last_day = (range_end - timedelta(microseconds=1)).date()
    for day in _daterange(range_start.date(), last_day + timedelta(days=1)):
        win_start = datetime.combine(day, day_start)
        win_end = datetime.combine(day, day_end)
        clipped_start = max(win_start, range_start)
        clipped_end = min(win_end, range_end)
        if clipped_start < clipped_end:
            daily_windows.append((clipped_start, clipped_end))

    raw_blocks: list[tuple[datetime, datetime]] = []
    for permit in permits:
        block_start = max(permit.start, range_start)
        block_end = min(permit.end, range_end)
        if block_start < block_end:
            raw_blocks.append((block_start, block_end))
    merged_blocks = _merge_intervals(raw_blocks)

    free: list[TimeWindow] = []
    busy: list[TimeWindow] = []
    for win in daily_windows:
        for gap_start, gap_end in _subtract(win, merged_blocks):
            duration_min = int((gap_end - gap_start).total_seconds() // 60)
            if duration_min >= min_slot_minutes:
                free.append(TimeWindow(start=gap_start, end=gap_end))
        for block_start, block_end in merged_blocks:
            clipped_start = max(block_start, win[0])
            clipped_end = min(block_end, win[1])
            if clipped_start < clipped_end:
                busy.append(TimeWindow(start=clipped_start, end=clipped_end))

    return free, busy
