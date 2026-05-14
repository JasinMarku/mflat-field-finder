"""Tests for sport normalization and Borough parsing."""

from __future__ import annotations

import pytest

from app.domain.sports import sport_from_permit_text, sports_from_catalog_row
from app.models import Borough, Sport


@pytest.mark.parametrize(
    "text,expected",
    [
        (" Soccer - Non Regulation", Sport.SOCCER),
        (" Soccer -Regulation", Sport.SOCCER),
        ("Flag Football - Youth", Sport.FLAG_FOOTBALL),
        ("Football - Youth", Sport.FOOTBALL),
        (" Softball (Little league)", Sport.SOFTBALL),
        (" Baseball - Adults", Sport.BASEBALL),
        (" Volleyball", Sport.VOLLEYBALL),
        (" Frisbee", Sport.FRISBEE),
        ("Ultimate", Sport.FRISBEE),
        ("Some unknown event", Sport.OTHER),
        ("", Sport.OTHER),
        ("   ", Sport.OTHER),
    ],
)
def test_sport_from_permit_text(text: str, expected: Sport) -> None:
    assert sport_from_permit_text(text) is expected


def test_sports_from_catalog_row_mixed_types() -> None:
    row = {
        "regulation_soccer": True,
        "nonregulation_soccer": "false",
        "adult_baseball": "true",
        "basketball": False,
        "tennis": "True",
        "handball": "FALSE",
        "ll_softball": True,
        "adult_football": "true",
        "flagfootball": True,
        "bocce": None,
    }
    sports = sports_from_catalog_row(row)
    assert Sport.SOCCER in sports
    assert Sport.BASEBALL in sports
    assert Sport.SOFTBALL in sports
    assert Sport.FOOTBALL in sports
    assert Sport.FLAG_FOOTBALL in sports
    assert Sport.TENNIS in sports
    assert Sport.BASKETBALL not in sports
    assert Sport.HANDBALL not in sports
    assert Sport.BOCCE not in sports


def test_sports_from_catalog_row_empty() -> None:
    assert sports_from_catalog_row({}) == frozenset()


@pytest.mark.parametrize(
    "code,expected",
    [
        (None, Borough.UNKNOWN),
        ("", Borough.UNKNOWN),
        ("m", Borough.MANHATTAN),
        ("M", Borough.MANHATTAN),
        (" b ", Borough.BROOKLYN),
        ("Q", Borough.QUEENS),
        ("X", Borough.BRONX),
        ("R", Borough.STATEN_ISLAND),
        ("Z", Borough.UNKNOWN),
    ],
)
def test_borough_from_code(code, expected: Borough) -> None:
    assert Borough.from_code(code) is expected


def test_borough_label() -> None:
    assert Borough.MANHATTAN.label == "Manhattan"
    assert Borough.STATEN_ISLAND.label == "Staten Island"
    assert Borough.UNKNOWN.label == "Unknown"
